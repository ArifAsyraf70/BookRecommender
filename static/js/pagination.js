
document.addEventListener("DOMContentLoaded", () => {
    const itemsPerPage = 12;
    const bookCards = document.querySelectorAll(".book-card");
    const totalPages = Math.ceil(bookCards.length / itemsPerPage);
    const paginationContainer = document.createElement("div");
    paginationContainer.classList.add("pagination");
    
    function showPage(page) {
        bookCards.forEach((card, index) => {
            card.style.display = (index >= (page - 1) * itemsPerPage && index < page * itemsPerPage) ? "block" : "none";
        });
    }
    
    for (let i = 1; i <= totalPages; i++) {
        const button = document.createElement("button");
        button.textContent = i;
        button.addEventListener("click", () => showPage(i));
        paginationContainer.appendChild(button);
    }
    
    document.body.appendChild(paginationContainer);
    showPage(1); // Show the first page initially
});
