// Update likes heart icon and text
function update_likes(btn, other_btn_id, text) {
    // Get likes's text element
    let likes_text = document.getElementById(text);
    console.log(likes_text)
    let likes = 'likes'

    // Change button
    btn.style.display = 'none';
    let other_btn = document.getElementById(other_btn_id);
    console.log(other_btn);
    other_btn.style.display = 'inline-block';

    if (parseInt(likes_text.textContent) + 1 == 1) {
        likes = ' like'
        likes_text.textContent = parseInt(likes_text.textContent) + 1 + likes;
    }
    if (parseInt(likes_text.textContent) - 1 == 1) {
        likes = ' like'
        likes_text.textContent = parseInt(likes_text.textContent) + 1 + likes;
    }
    else 
    {
        if (other_btn.style.color == 'red') {
            // Add 1 to likes count
            likes_text.textContent = parseInt(likes_text.textContent) - 1 + ' likes';
        }
        else {
             // Substract 1 to likes count
             likes_text.textContent = parseInt(likes_text.textContent) - 1 + ' likes';
        }
    }
}

// Add extra file input button
function addFileInput(input) {
    // Verify a file has been uploaded
    if (input.files.length > 0) {
        // Create a new file input element
        var newInput = document.createElement('input');
        newInput.type = 'file';
        newInput.name = 'files';
        newInput.className = 'form-control';
        newInput.onchange = function() { addFileInput(this); };

        // Append new input to the div
        document.getElementById('filesContainer').appendChild(newInput);
    }
}

// Update follow button
function update_follow_button(button, other_button_id) {
    // Change buttons display visibility
    button.style.display = 'none';
    let other_button = document.getElementById(other_button_id)
    console.log(other_button)
    other_button.style.display = 'inline-block'
}
