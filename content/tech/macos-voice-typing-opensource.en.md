+++
date = '2026-04-10T16:00:00-04:00'
title = 'I Built an Open-Source macOS Voice Typing Tool'
summary = "Typeless charges $12/month for a straightforward feature set, so I built a free alternative. Hotkeys, permissions, audio recording, status feedback, text insertion — five modules that each looked simple and each fought back. A record of the technical choices, pitfalls, and design decisions along the way."
categories = ["Tech"]
tags = ["macos", "speech-to-text", "open-source", "swift", "side-project"]
ShowToc = true
TocOpen = true
+++

Typeless nailed the interaction — press a key to start recording, press again to stop, and the text appears at your cursor. But $12/month, $144/year. The core pipeline is just hotkey, record, transcribe, paste. I decided to build my own.

I thought I'd finish in a weekend. In practice, five separate pitfalls stood between the first line of code and daily use, and every one of them came down to "the code was fine — I didn't understand how macOS actually works."

---

## The Big Picture

The app lives in the menu bar. At its core is a state machine:

```
idle → [hotkey press] → recording → [hotkey press] → processing → idle
                            ↓
                      [double-tap]
                            ↓
                          idle
```

Press the hotkey once and recording starts — a small overlay appears at the bottom of the screen showing audio levels. Press again and the recording is sent to the OpenAI Whisper API for transcription. The text is pasted at the cursor. If there's no active text field, a floating panel shows the result instead.

Tech stack:

| Layer | Technology | Why |
|-------|-----------|-----|
| App framework | Swift + SwiftUI + AppKit | Native feel, MenuBarExtra for menu bar residence |
| Audio recording | AVAudioRecorder (M4A, 44.1 kHz mono) | System handles format negotiation — most stable option |
| Transcription | MacPaw/OpenAI Swift SDK | Most active community OpenAI SDK; handles multipart encoding |
| Global hotkey | CGEvent tap | Only approach that supports modifier-only keys (e.g., Right Alt alone) |
| Text injection | Clipboard + simulated Cmd+V → popup fallback | Best compatibility across apps |
| Progress overlay | Pure AppKit (NSPanel + NSView + CALayer) | SwiftUI crashes in this scenario — more on that below |

Every "why" in that table has a wrong turn behind it.

---

## Hotkeys: CGEvent Tap and the Modifier-Only Problem

I assumed registering a global hotkey was a one-liner.

First problem: conflicts. `Cmd+Shift+R` was taken by my screenshot tool. `Ctrl+Space` was taken by the input method. A three-key combo worked but was annoying to press. Voice typing is a high-frequency action — nobody wants to hit three keys every time.

I settled on a single modifier key: Right Option (Alt). One key, no conflicts. But the standard macOS hotkey API doesn't support "just a modifier key" as a trigger. Modifiers are modifiers to the system, not keys.

The fix was CGEvent tap — one level below the normal hotkey API, intercepting the raw system event stream. It sees every keyboard event, including bare modifier presses. But that means handling every edge case yourself: modifier pressed then another key follows (the user is typing a combo, not triggering recording), rapid double-tap (cancel recording), distinguishing left from right modifiers (on my Windows keyboard plugged into a Mac, Right Ctrl and Right Alt share the same key code).

Later I added custom hotkey recording. The user clicks "Record," presses their preferred key, done. Sounds simple, but the global hotkey listener intercepts the key event before the recording component can see it. Fix: pause the global listener during recording, resume after.

This pattern of "two subsystems fighting each other" kept coming back.

---

## Permissions: Not a Code Bug — a Mental-Model Bug

macOS requires Accessibility permission before an app can listen for global hotkeys. Grant it once and you're set — or so I thought.

Every time I recompiled and ran the app, the hotkey stopped working. System Settings still showed the permission as enabled. I spent hours changing the hotkey logic, trying different registration approaches, adding debug logs.

The actual cause: each build produces a new binary with a new code signature. macOS treats it as a different app, so the old permission grant no longer applies. Not a code bug. A gap in my understanding of the macOS security model.

The fix is in the README: check "Automatically manage signing" in Xcode and select your Personal Team. This keeps the signature stable across builds so the permission sticks. No paid Apple Developer account needed — a free Apple ID works.

Microphone permission had a similar blind spot. When running from Xcode, macOS needs the microphone grant on Xcode itself, not on the compiled app.

These two permission issues cost nearly a full day. The lesson was clear: **when code looks correct but doesn't work, question your understanding of the system before questioning the code.**

---

## Audio: From AVAudioEngine to AVAudioRecorder

Recording should have been the simplest step. I spent the most time on it.

Version one used AVAudioEngine — Apple's "modern" audio framework with real-time processing, format conversion, and multi-node chaining. The documentation reads beautifully. Reality was a stream of errors: tap format mismatches, device initialization failures, engine startup exceptions. I tried at least six or seven configurations and referenced several open-source projects.

At one point every approach had failed. The cause turned out to be a loose USB microphone — the system had no input device at all. Not a code problem. A physical-world problem.

The final solution was AVAudioRecorder — Apple's older, simpler recording interface. One class, specify the format (M4A, AAC, 44.1 kHz mono), call `record()`, call `stop()`, get a file. The system handles all format negotiation.

AVAudioEngine can do far more than AVAudioRecorder. But I didn't need real-time processing or multi-node chains. I just needed "record audio, save to file." The dumbest approach was the best fit.

I chose M4A over WAV because AVAudioRecorder supports it natively and the Whisper API accepts it directly — no format conversion needed. Files are 10x smaller, uploads are faster.

---

## Progress Overlay: SwiftUI Crashed Here

Typeless has one critical design detail: a small overlay at the bottom of the screen during recording, showing status and audio levels. Without it, the user talks for a minute and has no idea whether anything was captured.

Version one used SwiftUI's ObservableObject to drive the overlay UI. Recording state changes update `@Published` properties, SwiftUI refreshes the view. Standard pattern.

But in this case, ObservableObject updates and CGEvent tap callbacks run on different actors — one on MainActor, one on the system event thread. Swift's actor isolation checks crashed the app.

This wasn't a coding mistake. SwiftUI's concurrency model and CGEvent tap's low-level callback mechanism have a fundamental conflict. I tried every combination of `@MainActor` annotations and `DispatchQueue.main.async` wrappers. Either the app crashed or the audio level updates lagged visibly.

I gave up on SwiftUI and rewrote the overlay in pure AppKit: NSPanel as the window (doesn't steal focus), NSView with manual layout, CALayer for the audio-level pulse animation. Twice the code. Stable.

**"Newer" doesn't mean "better."** SwiftUI works well for most UI. But when you need deep interaction with low-level system mechanisms, its abstraction layer becomes an obstacle. The right question isn't "is this the latest framework?" — it's "does this work reliably in this specific scenario?"

---

## Text Insertion: Combinatorial Complexity in a "Simple" Problem

Transcription done, text in hand, paste at the cursor. Sounds like the easiest final step.

Version one used the macOS Accessibility API to set the text field's value directly. The call returned success, but some apps (Terminal, for example) did nothing — AXUIElement reported "set succeeded" while the content stayed unchanged. This is a known Accessibility API behavior: some apps have incomplete AXUIElement implementations.

I switched to clipboard: write text to the pasteboard, simulate Cmd+V. Much better compatibility, but a new problem — pasting overwrites whatever the user had on the clipboard. Fix: save the clipboard before pasting, restore it after.

Another issue: if the cursor isn't in a text field when recording stops (say, a blank area in a browser), the paste executes but nothing receives it. The user thinks transcription failed.

The final design is a fallback chain:

1. The instant recording stops, `OutputTargetSnapshot` captures the focused UI element and app PID
2. After transcription, check whether the snapshot's element has an editable area (`hasTextInput`)
3. Yes → clipboard + Cmd+V paste
4. No → show a floating panel with the text and a Copy button

Why capture the snapshot when recording stops instead of after transcription? Transcription takes a few seconds. The user might switch windows while waiting. Detecting focus after transcription could paste into the wrong place.

I also found a bug while testing in the app's own settings window: text appeared twice. The settings view had its own SwiftUI text binding, and the clipboard paste triggered a second update — two paths fired simultaneously. Fix: disable the global insertion logic inside the settings window.

Each problem was easy in isolation. But cursor position, app type, and text-field state create a large matrix of combinations, each needing its own verification.

---

## Design Decisions in Hindsight

Looking back, several decisions I'd make again:

**Toggle mode instead of press-and-hold.** The original design was hold-to-record, release-to-stop. I switched to toggle (press once to start, press once to stop) for two reasons: recording can last tens of seconds and holding a key that long is tiring; toggle lets users take both hands off the keyboard and talk naturally. Double-tap cancel comes free with toggle — tap twice fast, recording is discarded, back to idle.

**Cutting the translation feature.** I initially planned transcription plus translation, meaning two API keys (Whisper for transcription, GPT for translation). I thought about it and realized I rarely use translation myself. After cutting it, only one key is needed, setup steps halved, code complexity dropped by a third. Fewer features, better experience.

**MacPaw/OpenAI SDK instead of hand-written HTTP.** Version one hand-built multipart/form-data requests. I spent real time on encoding boundaries. Switching to MacPaw's Swift SDK made it a single function call with better error handling. For work that isn't a core differentiator, use a community solution and save time.

**Remote API instead of a local model.** I tried WhisperKit — a 500 MB model running locally, no network needed. But it kept misrecognizing Chinese as English during mixed-language input. The remote API is a tier more accurate, with acceptable latency (2–4 seconds). Cost is low — details below.

---

## Cost

Default model: `gpt-4o-mini-transcribe`.

| Usage | Cost |
|-------|------|
| 1 minute (~150 words) | $0.003 |
| 30 minutes/day for a month | $2.70 |
| 5 minutes/day for a month (my actual usage) | $0.45 |

Typeless charges $12/month. Even heavy use is an order of magnitude cheaper.

---

## Takeaways

The biggest lesson from this project: **don't underestimate "simple" things.**

"Hotkey, record, transcribe, paste" — a one-sentence spec. In practice it touches CGEvent tap, Accessibility API, AVAudioRecorder, code signing, and actor isolation. Each layer has its own temperament, and they fight each other. The hotkey listener fights the hotkey recorder. SwiftUI fights CGEvent tap. The Accessibility API fights individual apps' implementations.

The deeper realization: **most time went to understanding the system, not building features.** Why did the permission break? Why did recording fail? Why did the overlay crash? The answers were never in the code — they were in macOS internals. There's no shortcut for this kind of learning. You just step on the mines one by one.

One last thing: **start with the dumb approach.** AVAudioRecorder is dumber than AVAudioEngine. AppKit is dumber than SwiftUI. Clipboard paste is dumber than the Accessibility API. All three are the solutions that survived. Every time I tried the "more elegant" option first, I took a detour. Get it working, then refine — not a platitude, but a conclusion this project proved repeatedly.

MIT licensed: [github.com/scinttt/open-typeless-formac](https://github.com/scinttt/open-typeless-formac)
