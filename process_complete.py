with open('shared_completed.txt', 'r') as file:
    # Extract all lines, stripping extra whitespace
    urls = [line.strip() for line in file if line.strip()]

# Convert the list to a set to remove duplicates, then back to a list
unique_urls = list(set(urls))

# Count the unique elements
unique_count = len(unique_urls)

print(f"Found {unique_count} unique elements.")

# Save the unique elements to a new text file
with open('unique_urls_list.txt', 'w') as out_file:
    for url in unique_urls:
        out_file.write(url + '\n')