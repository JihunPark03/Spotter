document.addEventListener('mouseup', () => {
    const selectedText = window.getSelection().toString().trim();
  
    if (selectedText.length > 0) {
      chrome.runtime.sendMessage({
        type: 'save_selection',
        text: selectedText
      });
    }
  });