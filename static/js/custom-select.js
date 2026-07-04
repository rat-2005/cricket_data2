function convertToCustomMultiSelect(selectId) {
    const originalSelect = document.getElementById(selectId);
    if (!originalSelect) return;
    
    // If it's already a custom select wrapper, update options only if needed. For now, let's just rebuild it.
    if (originalSelect.parentElement.classList.contains('custom-multi-wrapper')) {
        revertCustomMultiSelect(selectId); // Tear down and rebuild so it's fresh
    }

    // Ensure it's treated as multiple
    originalSelect.multiple = true;

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
    
    // Add Search input area
    const searchWrapper = document.createElement('div');
    searchWrapper.className = 'custom-multi-search-wrapper';
    
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = 'Search...';
    searchInput.className = 'custom-multi-search-input';
    
    const selectMatchingLabel = document.createElement('label');
    selectMatchingLabel.className = 'custom-multi-select-all';
    
    const selectMatchingCheckbox = document.createElement('input');
    selectMatchingCheckbox.type = 'checkbox';
    
    const selectMatchingText = document.createElement('span');
    selectMatchingText.innerText = 'Select Matching';
    
    selectMatchingLabel.appendChild(selectMatchingCheckbox);
    selectMatchingLabel.appendChild(selectMatchingText);
    
    searchWrapper.appendChild(searchInput);
    searchWrapper.appendChild(selectMatchingLabel);
    dropdown.appendChild(searchWrapper);

    const optionsContainer = document.createElement('div');
    optionsContainer.className = 'custom-multi-options';
    
    const optionDivs = [];
    
    // Create checkboxes for each option
    Array.from(originalSelect.options).forEach(opt => {
        const optionDiv = document.createElement('label');
        optionDiv.className = 'custom-multi-option';
        optionDiv.dataset.value = opt.value.toLowerCase();
        optionDiv.dataset.text = opt.text.toLowerCase();
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = opt.value;
        checkbox.checked = opt.selected;
        
        const labelText = document.createElement('span');
        labelText.innerText = opt.text;
        
        optionDiv.appendChild(checkbox);
        optionDiv.appendChild(labelText);
        
        // Handle "All" logic
        checkbox.addEventListener('change', (e) => {
            opt.selected = e.target.checked;
            
            if (opt.value === 'All') {
                if (e.target.checked) {
                    // Uncheck all other options
                    optionDivs.forEach(div => {
                        const cb = div.querySelector('input[type="checkbox"]');
                        if (cb.value !== 'All') {
                            cb.checked = false;
                            const originalOpt = Array.from(originalSelect.options).find(o => o.value === cb.value);
                            if (originalOpt) originalOpt.selected = false;
                        }
                    });
                }
            } else {
                if (e.target.checked) {
                    // Uncheck "All"
                    const allCb = optionDivs.find(div => div.querySelector('input[type="checkbox"]').value === 'All');
                    if (allCb) {
                        allCb.querySelector('input[type="checkbox"]').checked = false;
                        const originalOpt = Array.from(originalSelect.options).find(o => o.value === 'All');
                        if (originalOpt) originalOpt.selected = false;
                    }
                } else {
                    // If everything is unchecked, check "All"
                    const anyChecked = optionDivs.some(div => {
                        const cb = div.querySelector('input[type="checkbox"]');
                        return cb.value !== 'All' && cb.checked;
                    });
                    
                    if (!anyChecked) {
                        const allCb = optionDivs.find(div => div.querySelector('input[type="checkbox"]').value === 'All');
                        if (allCb) {
                            allCb.querySelector('input[type="checkbox"]').checked = true;
                            const originalOpt = Array.from(originalSelect.options).find(o => o.value === 'All');
                            if (originalOpt) originalOpt.selected = true;
                        }
                    }
                }
            }
            
            updateHeaderText();
            updateSelectMatchingState();
        });
        
        optionDivs.push(optionDiv);
        optionsContainer.appendChild(optionDiv);
    });
    
    // Check "All" by default if nothing is selected
    const anyChecked = optionDivs.some(div => div.querySelector('input[type="checkbox"]').checked);
    if (!anyChecked) {
        const allCb = optionDivs.find(div => div.querySelector('input[type="checkbox"]').value === 'All');
        if (allCb) {
            allCb.querySelector('input[type="checkbox"]').checked = true;
            const originalOpt = Array.from(originalSelect.options).find(o => o.value === 'All');
            if (originalOpt) originalOpt.selected = true;
        }
    }

    // Search functionality
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        optionDivs.forEach(div => {
            const isMatch = div.dataset.text.includes(query) || div.dataset.value.includes(query);
            div.style.display = isMatch ? 'flex' : 'none';
        });
        updateSelectMatchingState();
    });

    // Select Matching functionality
    selectMatchingCheckbox.addEventListener('change', (e) => {
        const checkAll = e.target.checked;
        let changed = false;
        
        optionDivs.forEach(div => {
            if (div.style.display !== 'none' && div.querySelector('input[type="checkbox"]').value !== 'All') {
                const cb = div.querySelector('input[type="checkbox"]');
                if (cb.checked !== checkAll) {
                    cb.checked = checkAll;
                    const originalOpt = Array.from(originalSelect.options).find(o => o.value === cb.value);
                    if (originalOpt) originalOpt.selected = checkAll;
                    changed = true;
                }
            }
        });
        
        if (changed) {
            // Check if any non-All is checked to manage the "All" checkbox state
            const anyChecked = optionDivs.some(div => {
                const cb = div.querySelector('input[type="checkbox"]');
                return cb.value !== 'All' && cb.checked;
            });
            
            const allCb = optionDivs.find(div => div.querySelector('input[type="checkbox"]').value === 'All');
            if (allCb) {
                const acb = allCb.querySelector('input[type="checkbox"]');
                const prev = acb.checked;
                acb.checked = !anyChecked;
                const originalOpt = Array.from(originalSelect.options).find(o => o.value === 'All');
                if (originalOpt) originalOpt.selected = !anyChecked;
            }
            updateHeaderText();
        }
    });

    function updateSelectMatchingState() {
        // If all visible (non-All) options are checked, tick the box
        const visibleDivs = optionDivs.filter(div => div.style.display !== 'none' && div.querySelector('input[type="checkbox"]').value !== 'All');
        if (visibleDivs.length === 0) {
            selectMatchingCheckbox.checked = false;
            return;
        }
        
        const allVisibleChecked = visibleDivs.every(div => div.querySelector('input[type="checkbox"]').checked);
        selectMatchingCheckbox.checked = allVisibleChecked;
    }
    
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
    
    // Event Listeners for Custom UI
    function updateHeaderText() {
        const selectedOptions = Array.from(originalSelect.selectedOptions);
        const isNot = originalSelect.dataset.not === "true";
        const prefix = isNot ? 'Not ' : '';
        
        selectedOptions.forEach(opt => {
            if (opt.text.startsWith('Not ')) opt.text = opt.text.replace('Not ', '');
        });

        if (selectedOptions.length === 0) {
            headerText.innerText = 'Select Options...';
        } else {
            const joinedText = selectedOptions.map(opt => {
                let txt = opt.text;
                if (txt.startsWith('Not ')) txt = txt.replace('Not ', '');
                return prefix + txt;
            }).join(', ');
            
            headerText.innerText = joinedText;
        }
    }
    
    // Listen for external changes on original select (like when toggleNot fires change event)
    originalSelect.addEventListener('change', () => {
        // We might need to resync checkboxes if changed externally
        Array.from(originalSelect.options).forEach(opt => {
            const cb = optionDivs.find(div => div.querySelector('input').value === opt.value);
            if (cb) cb.querySelector('input').checked = opt.selected;
        });
        updateHeaderText();
        updateSelectMatchingState();
    });
    
    // Listen for 'syncui' custom event (fired by setFilterVal) to resync checkboxes
    // without triggering the filter cascade that 'change' would cause
    originalSelect.addEventListener('syncui', () => {
        Array.from(originalSelect.options).forEach(opt => {
            const cb = optionDivs.find(div => div.querySelector('input').value === opt.value);
            if (cb) cb.querySelector('input').checked = opt.selected;
        });
        updateHeaderText();
        updateSelectMatchingState();
    });
    
    header.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('active');
        if (dropdown.classList.contains('active')) {
            searchInput.focus();
        }
    });
    
    doneBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.remove('active');
        // Trigger a change event so the backend updates
        originalSelect.dispatchEvent(new Event('change'));
    });
    
    // Close when clicking outside
    document.addEventListener('click', (e) => {
        if (!wrapper.contains(e.target)) {
            dropdown.classList.remove('active');
        }
    });

    updateHeaderText();
    updateSelectMatchingState();
}

function revertCustomMultiSelect(selectId) {
    const originalSelect = document.getElementById(selectId);
    if (!originalSelect || !originalSelect.parentElement.classList.contains('custom-multi-wrapper')) return;
    
    const wrapper = originalSelect.parentElement;
    
    // Move original select back to its original parent
    wrapper.parentNode.insertBefore(originalSelect, wrapper);
    
    // Show original select, remove multiple attribute
    originalSelect.style.display = '';
    
    // Remove custom wrapper
    wrapper.remove();
}

function initializeAllCustomSelects() {
    document.querySelectorAll('select[id^="filter"]').forEach(select => {
        convertToCustomMultiSelect(select.id);
    });
}

function resetFilters() {
    document.querySelectorAll('.custom-multi-wrapper select').forEach(select => {
        Array.from(select.options).forEach(opt => {
            opt.selected = (opt.value === 'All');
        });
        select.dataset.not = "false";
        select.dispatchEvent(new Event('change'));
    });
    
    // Also reset all toggle-not buttons
    document.querySelectorAll('.filter-btn.active-not').forEach(btn => {
        btn.classList.remove('active-not');
    });
    
    // Clear all search inputs
    document.querySelectorAll('.custom-multi-search-input').forEach(input => {
        input.value = '';
        input.dispatchEvent(new Event('input'));
    });
}
