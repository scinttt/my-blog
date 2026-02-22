import os
import sys

def check_summaries(content_dir):
    missing_summary = []
    total_files = 0
    for root, dirs, files in os.walk(content_dir):
        # Skip hidden directories like .git
        if any(part.startswith('.') for part in root.split(os.sep)):
            continue
            
        for file in files:
            if not file.endswith('.md'):
                continue
            
            total_files += 1
            path = os.path.join(root, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    if content.startswith('+++'):
                        end_index = content.find('+++', 3)
                        if end_index != -1:
                            front_matter = content[3:end_index]
                            if 'summary =' not in front_matter and 'summary=' not in front_matter:
                                missing_summary.append(path)
                        else:
                            missing_summary.append(f"{path} (Invalid TOML)")
                    elif content.startswith('---'):
                        end_index = content.find('---', 3)
                        if end_index != -1:
                            front_matter = content[3:end_index]
                            if 'summary:' not in front_matter:
                                missing_summary.append(path)
                        else:
                            missing_summary.append(f"{path} (Invalid YAML)")
                    else:
                        missing_summary.append(f"{path} (No front matter)")
            except Exception as e:
                missing_summary.append(f"{path} (Error: {e})")
    
    if missing_summary:
        print(f"Total files: {total_files}")
        print(f"Missing summary ({len(missing_summary)}):")
        for p in missing_summary:
            print(f"  - {p}")
        return False
    else:
        print(f"All {total_files} files have a summary field.")
        return True

if __name__ == "__main__":
    if not os.path.exists('content'):
        print("'content' directory not found.")
        sys.exit(1)
    if check_summaries('content'):
        sys.exit(0)
    else:
        sys.exit(1)
