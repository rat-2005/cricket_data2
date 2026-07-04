with open('templates/faceoff.html', encoding='utf-8') as f:
    for i, line in enumerate(f):
        for kw in ['loadingState', 'mainContent', 'emptyState']:
            if f'id="{kw}"' in line:
                print(f'Line {i+1} ({kw}): {line.strip()[:120]}')
