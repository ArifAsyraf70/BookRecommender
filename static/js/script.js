document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.getElementById("search-input");
    const suggestions = document.getElementById("suggestions");

    if (searchInput && suggestions) {
        // For normal search, use /search and query parameter "query"
        setupSearchSuggestions(searchInput, suggestions, "/search", "query");
    }

    const recommenderSearchInput = document.getElementById("recommender-search-input");
    const recommenderSuggestions = document.getElementById("recommender-suggestions");

    if (recommenderSearchInput && recommenderSuggestions) {
        // For recommender, use /recommender and query parameter "title"
        setupSearchSuggestions(recommenderSearchInput, recommenderSuggestions, "/recommender", "title");
    }
});



function setupSearchSuggestions(inputElement, suggestionsElement, targetRoute, paramName = "query") {
    inputElement.addEventListener("input", async (e) => {
        const query = e.target.value.trim();
        if (query.length < 2) {
            suggestionsElement.classList.remove("active");
            suggestionsElement.innerHTML = "";
            return;
        }

        try {
            const response = await fetch(`/search_suggestions?query=${query}`);
            const results = await response.json();

            if (results.length > 0) {
                // Dynamically set the target route and query parameter name
                suggestionsElement.innerHTML = results
                    .map((book) => `<li><a href="${targetRoute}?${paramName}=${encodeURIComponent(book)}">${book}</a></li>`)
                    .join("");
                suggestionsElement.classList.add("active");
            } else {
                suggestionsElement.classList.remove("active");
                suggestionsElement.innerHTML = "";
            }
        } catch (error) {
            console.error("Error fetching suggestions:", error);
        }
    });

    inputElement.addEventListener("blur", () => {
        setTimeout(() => {
            suggestionsElement.classList.remove("active");
            suggestionsElement.innerHTML = "";
        }, 200);
    });

    suggestionsElement.addEventListener("mousedown", (e) => {
        e.preventDefault();
    });
}

const searchInput = document.getElementById("search-input");
const suggestionsBox = document.getElementById("suggestions");

searchInput.addEventListener("input", () => {
    const query = searchInput.value.trim();
    if (query.length > 1) {
        suggestionsBox.style.display = "block"; // Show suggestions when typing
        // Fetch suggestions dynamically (use your existing logic here)
    } else {
        suggestionsBox.style.display = "none"; // Hide suggestions if no input
    }
});

searchInput.addEventListener("blur", () => {
    setTimeout(() => {
        suggestionsBox.style.display = "none"; // Hide suggestions when losing focus
    }, 200);
});



function logBook(book) {
    fetch('/log_book', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(book),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data.message);
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Example usage: Log a book when the user views it
const book = {
    title: "The Great Gatsby",
    author: "F. Scott Fitzgerald",
    category: "Fiction",
    thumbnail: "path/to/thumbnail.jpg",
    average_rating: 4.2,
};
logBook(book);


