// Update likes heart icon and text
function update_likes(like_button, text)
{
    // Get likes's text element
    let likes_text = document.getElementById(text);
    let likes = 'likes'

    // Change icon color
    if (like_button.style.color != 'red') {
        // Change icon color
        like_button.style.color = 'red';
        // Change icon class to be a solid heart
        like_button.querySelector("#icon").className = 'fa-solid fa-heart';
        // Change icon's text to 'Like'
        like_button.querySelector("#text").textContent = ' Liked';
        // Add +1 to likes count
        if (parseInt(likes_text.textContent) + 1 == 1) {
            likes = ' like'
        }
        likes_text.textContent = parseInt(likes_text.textContent) + 1 + likes;
    }
    else {
        // Change icon color
        like_button.style.color = 'black';
        // Change icon class to be a empty heart
        like_button.querySelector("#icon").className = 'fa-regular fa-heart';
        // Change icon's text to 'Like'
        like_button.querySelector("#text").textContent = ' Like';
        // Substract -1 to likes count
        likes_text.textContent = parseInt(likes_text.textContent) - 1 + ' likes';

    }
}
