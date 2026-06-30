function convertToCustomMultiSelect(selectId) {
    const originalSelect = document.getElementById(selectId);
    if (!originalSelect) return;
    
    // If it's already a custom select wrapper, do nothing
    if (originalSelect.parentElement.classList.contains('custom-multi-wrapper')) return;

    // Create wrapper
    const wrapper = document.createElement('div');
    wrapper.className = 'custom-multi-wrapper';
    
    // Create header (acts like the select box)
    const header = document.createElement('div');
    header.className = 'custom-multi-header';
    const headerText = document.createElement('span');
    headerText.innerText = 'Select Options...';
    
    const chevron = document.createElement('i');
    chevron.className = 'fas fa-chevron-down';
    
    header.appendChild(headerText);
    header.appendChild(chevron);
    
    // Create dropdown panel
    const dropdown = document.createElement('div');
    dropdown.className = 'custom-multi-dropdown';
    
    const optionsContainer = document.createElement('div');
    optionsContainer.className = 'custom-multi-options';
    
    // Create checkboxes for each option
    Array.from(originalSelect.options).forEach(opt => {
        const optionDiv = document.createElement('label');
        optionDiv.className = 'custom-multi-option';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = opt.value;
        checkbox.checked = opt.selected;
        
        const labelText = document.createElement('span');
        labelText.innerText = opt.text;
        
        optionDiv.appendChild(checkbox);
        optionDiv.appendChild(labelText);
        
        // Sync custom UI to original select
        checkbox.addEventListener('change', (e) => {
            opt.selected = e.target.checked;
            updateHeaderText();
        });
        
        optionsContainer.appendChild(optionDiv);
    });
    
    // Create footer with Done button
    const footer = document.createElement('div');
    footer.className = 'custom-multi-footer';
    const doneBtn = document.createElement('button');
    doneBtn.className = 'custom-multi-btn';
    doneBtn.innerText = 'Done';
    footer.appendChild(doneBtn);
    
    dropdown.appendChild(optionsContainer);
    dropdown.appendChild(footer);
    
    // Assemble the DOM
    originalSelect.parentNode.insertBefore(wrapper, originalSelect);
    wrapper.appendChild(header);
    wrapper.appendChild(dropdown);
    wrapper.appendChild(originalSelect);
    
    // Hide original select
    originalSelect.style.display = 'none';
    originalSelect.multiple = true;
    
    // Event Listeners for Custom UI
    function updateHeaderText() {
        const selectedOptions = Array.from(originalSelect.selectedOptions);
        const isNot = originalSelect.dataset.not === "true";
        const prefix = isNot ? 'Not ' : '';
        
        // Ensure options text does not have "Not " permanently added if it leaked from single mode
        selectedOptions.forEach(opt => {
            if (opt.text.startsWith('Not ')) opt.text = opt.text.replace('Not ', '');
        });

        if (selectedOptions.length === 0) {
            headerText.innerText = 'Select Options...';
        } else {
            // Join selected option texts, applying prefix to each if needed
            const joinedText = selectedOptions.map(opt => {
                let txt = opt.text;
                if (txt.startsWith('Not ')) txt = txt.replace('Not ', '');
                return prefix + txt;
            }).join(', ');
            
            // Optional: if it gets too long, we could truncate, but let's just use CSS text-overflow: ellipsis
            headerText.innerText = joinedText;
        }
    }
    
    // Listen for external changes on original select (like when toggleNot fires change event)
    originalSelect.addEventListener('change', updateHeaderText);
    
    header.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('active');
    });
    
    doneBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.remove('active');
        // Trigger a change event so the backend updates
        originalSelect.dispatchEvent(new Event('change'));
    });
    
    dropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });
    
    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });

    updateHeaderText();
}

function revertCustomMultiSelect(selectId) {
    const originalSelect = document.getElementById(selectId);
    if (!originalSelect || !originalSelect.parentElement.classList.contains('custom-multi-wrapper')) return;
    
    const wrapper = originalSelect.parentElement;
    
    // Move original select back to its original parent
    wrapper.parentNode.insertBefore(originalSelect, wrapper);
    
    // Show original select, remove multiple attribute
    originalSelect.style.display = '';
    originalSelect.multiple = false;
    
    // Remove custom wrapper
    wrapper.remove();
    
    // Trigger change for backend update
    originalSelect.dispatchEvent(new Event('change'));
}
