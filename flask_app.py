from flask import Flask, session, request, redirect, jsonify, render_template, send_from_directory, make_response, url_for
import pickle
import pandas as pd
import random
import os

# Load the pre-trained model and similarity matrix
with open('tfidf_model.pkl', 'rb') as f:
    tfidf_model = pickle.load(f)

with open('similarity_matrix.pkl', 'rb') as f:
    similarity_matrix = pickle.load(f)

# Load the book data
books = pd.read_csv('data/data.csv')

app = Flask(__name__)


# Secret key for sessions
app.secret_key = "supersecretkey"

# Configure session
app.config["SESSION_TYPE"] = "filesystem"  # Save session data on the server filesystem


@app.route('/set_name', methods=['GET', 'POST'])
def set_name():
    if request.method == 'POST':
        user_name = request.form.get('name')
        if user_name:
            session['user_name'] = user_name  # Save the name in the session
            return redirect(url_for('index'))
    return render_template('set_name.html')

@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('index'))




@app.route('/start_session', methods=['GET', 'POST'])
def start_session():
    if request.method == 'POST':
        user_name = request.form.get('name')
        if user_name:
            session['user_name'] = user_name  # Save the user's name in the session
            session['reading_history'] = []  # Initialize an empty reading history
            return redirect(url_for('index'))
    return render_template('start_session.html')




# Serve the index.html file
@app.route('/')
def index():
    # Get the user's name from the session
    user_name = session.get('user_name', None)

    # Include the DataFrame index as part of the book data
    all_books = books[['title', 'authors', 'categories', 'thumbnail', 'average_rating']].copy()
    all_books['index'] = books.index  # Add the DataFrame index to the book data

    # Replace null thumbnails with a default image
    all_books['thumbnail'] = all_books['thumbnail'].fillna('static/images/none.JPG')

    # Convert to a list of dictionaries for the template
    all_books = all_books.to_dict(orient='records')

    # Random recommendations
    random_books = books.sample(4)[['title', 'authors', 'categories', 'thumbnail', 'average_rating']].copy()
    random_books['index'] = random_books.index  # Include index for random books
    random_books['thumbnail'] = random_books['thumbnail'].fillna('static/images/none.JPG')
    random_books = random_books.to_dict(orient='records')

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 12
    total_pages = (len(all_books) + per_page - 1) // per_page
    paginated_books = all_books[(page - 1) * per_page: page * per_page]

    # Calculate previous and next pages
    previous_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None

    return render_template(
        'index.html',
        books=paginated_books,
        random_books=random_books,
        current_page=page,
        total_pages=total_pages,
        previous_page=previous_page,
        next_page=next_page,
        user_name=user_name  # Pass the user's name to the template
    )




from flask import flash

@app.route('/log_book', methods=['POST'])
def log_book():
    try:
        # Get book details from the form
        book_id = request.form.get("book_id")
        if not book_id or not book_id.isdigit():
            flash("Invalid book data. Unable to add to reading list.", "error")
            return redirect('/')

        book_id = int(book_id)
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        category = request.form.get("category", "").strip()
        thumbnail = request.form.get("thumbnail", "static/images/none.JPG").strip()
        average_rating = request.form.get("average_rating", "0.0").strip()

        # Check if the title or author is missing
        if not title or not author:
            flash("Invalid book data. Unable to add to reading list.", "error")
            return redirect('/')

        # Initialize reading history if not already present
        if "reading_history" not in session:
            session["reading_history"] = []

        # Append the book only if it does not already exist in the history
        book_data = {
            "book_id": book_id,
            "title": title,
            "author": author,
            "category": category,
            "thumbnail": thumbnail,
            "average_rating": average_rating,
        }
        if book_data not in session["reading_history"]:
            session["reading_history"].append(book_data)
            flash(f"'{title}' has been added to your reading list!", "success")
        else:
            flash(f"'{title}' is already in your reading list.", "info")

        session.modified = True  # Mark session as modified
        return redirect('/')
    except Exception as e:
        flash("An unexpected error occurred. Please try again.", "error")
        return redirect('/')










@app.route('/reading_history', methods=['GET'])
def reading_history():
    # Get reading history from session or set to empty list
    reading_history = session.get("reading_history", [])
    return render_template("reading_history.html", reading_history=reading_history)


@app.route('/clear_history', methods=['GET'])
def clear_history():
    session.pop("reading_history", None)
    return jsonify({"message": "Reading history cleared successfully!"})


@app.route('/remove_from_history', methods=['POST'])
def remove_from_history():
    # Get the book index from the form data
    book_index = int(request.form.get('book_index', -1))

    # Fetch the reading history from the session
    reading_history = session.get('reading_history', [])

    # Check if the index is valid
    if 0 <= book_index < len(reading_history):
        # Remove the book from the history
        reading_history.pop(book_index)
        # Update the session
        session['reading_history'] = reading_history

    # Redirect back to the reading history page
    return redirect('/reading_history')



# Update the search route to allow search by book title or author name
# Update the search route to allow search by book title or author name
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').lower()
    search_by = request.args.get('search_by', 'title')  # Get search type (default is title)

    if not query:
        return render_template('search.html', books=[], query=query, search_by=search_by)

    # Search logic
    if search_by == 'title':
        matching_books = books[books['title'].str.contains(query, case=False, na=False)]
    elif search_by == 'author':
        matching_books = books[books['authors'].str.contains(query, case=False, na=False)]
    else:
        matching_books = pd.DataFrame()  # Empty DataFrame if invalid search_by

    # Process the books for rendering
    book_list = matching_books[['title', 'authors', 'categories', 'thumbnail', 'average_rating']].copy()
    book_list['index'] = matching_books.index  # Include the original index

    # Handle missing thumbnails
    book_list['thumbnail'] = book_list['thumbnail'].apply(
        lambda x: x if pd.notna(x) else 'static/images/none.JPG'
    )

    return render_template(
        'search.html',
        books=book_list.to_dict(orient='records'),
        query=query,
        search_by=search_by
    )


@app.route('/search_suggestions', methods=['GET'])
def search_suggestions():
    query = request.args.get('query', '').lower()
    search_by = request.args.get('search_by', 'title')  # Get search type (default is title)

    if not query:
        return jsonify([])  # Return empty list if query is missing

    # Match titles or authors based on search_by
    if search_by == 'title':
        suggestions = books[books['title'].str.contains(query, case=False, na=False)]['title'].drop_duplicates().tolist()
    elif search_by == 'author':
        suggestions = books[books['authors'].str.contains(query, case=False, na=False)]['authors'].drop_duplicates().tolist()
    else:
        suggestions = []  # Empty list if invalid search_by

    # Return up to 5 suggestions
    return jsonify(suggestions[:5])







    
@app.route('/recommend_by_category', methods=['GET'])
def recommend_by_category():
    category = request.args.get('category')
    if not category:
        return jsonify({"error": "Please provide a category"}), 400

    # Filter books by the given category
    filtered_books = books[books['categories'].str.contains(category, case=False, na=False)]

    if filtered_books.empty:
        return jsonify({"error": "No books found for the given category"}), 404

    # Get a list of book titles from the filtered books
    recommended_books = filtered_books['title'].tolist()

    
    return jsonify({"recommendations": recommended_books})


@app.route('/recommend', methods=['GET'])
def recommend():
    book_title = request.args.get('title')
    if not book_title:
        return jsonify({"error": "Please provide a book title"}), 400

    # Find the book index
    try:
        idx = books[books['title'] == book_title].index[0]
    except IndexError:
        return jsonify({"error": "Book not found"}), 404

    # Get similarity scores
    sim_scores = list(enumerate(similarity_matrix[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Get the top 4 recommended books with thumbnails
    top_books = [
        {"title": books.iloc[i[0]]['title'], "thumbnail": books.iloc[i[0]]['thumbnail']}
        for i in sim_scores[1:5]  # Ensure only 4 recommendations
    ]

    # Debug: Log the number of books
    print(f"Number of recommendations: {len(top_books)}")

    return jsonify({"recommendations": top_books})





@app.route('/book/<int:book_id>', methods=['GET'])
def book_detail(book_id):
    try:
        # Retrieve the book details using the book ID
        book = books.iloc[book_id].to_dict()
        book['index'] = book_id  # Ensure the index is included
    except IndexError:
        # If the book ID doesn't exist, render a 404 page
        return render_template('404.html'), 404

    # Handle missing fields by adding default values
    book['isbn'] = book.get('isbn10', 'Not available')
    book['description'] = book.get('description', 'No description available.')
    book['thumbnail'] = book['thumbnail'] if book['thumbnail'] else 'static/images/none.JPG'

    # Convert published_year and num_pages to integers, if available
    try:
        book['published_year'] = int(float(book['published_year'])) if book['published_year'] != 'Not available' else 'Not available'
    except (ValueError, TypeError):
        book['published_year'] = 'Not available'

    try:
        book['number_of_pages'] = int(float(book['num_pages'])) if book['num_pages'] != 'Not available' else 'Not available'
    except (ValueError, TypeError):
        book['number_of_pages'] = 'Not available'

    # Render the book detail template with the prepared data
    return render_template('book_detail.html', book=book)



@app.route('/recommender', methods=['GET'])
def recommender():
    book_title = request.args.get('title', '').strip()
    
    if not book_title:
        return render_template('recommender.html', recommendations=[], book_title='', book_details={})

    # Validate if the book exists
    try:
        book_idx = books[books['title'] == book_title].index[0]
    except IndexError:
        return render_template('recommender.html', recommendations=[], book_title=book_title, error="Book not found.", book_details={})

    # Get similarity scores for the book
    sim_scores = list(enumerate(similarity_matrix[book_idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)

    # Fetch the top 4 similar books (excluding the current book)
    similar_books = [
        {
            "title": books.iloc[i[0]]['title'],
            "authors": books.iloc[i[0]]['authors'],
            "categories": books.iloc[i[0]]['categories'],
            "thumbnail": books.iloc[i[0]]['thumbnail'] if books.iloc[i[0]]['thumbnail'] else 'static/images/none.JPG',
            "average_rating": books.iloc[i[0]]['average_rating'],
            "index": i[0]
        }
        for i in sim_scores[1:5]
    ]

    # Fetch the current book's details
    book_details = {
    "title": books.iloc[book_idx]["title"],
    "authors": books.iloc[book_idx]["authors"],
    "categories": books.iloc[book_idx]["categories"],
    "thumbnail": books.iloc[book_idx]["thumbnail"] if books.iloc[book_idx]["thumbnail"] and books.iloc[book_idx]["thumbnail"] not in ['nan', 'Not available'] else "static/images/none.JPG",
    "average_rating": books.iloc[book_idx]["average_rating"],
    "index": book_idx,  # Ensure the index is included here
}


    return render_template('recommender.html', recommendations=similar_books, book_title=book_title, book_details=book_details)



@app.route('/filter_by_genre', methods=['GET'])
def filter_by_genre():
    genre = request.args.get('genre', '').strip().lower()
    
    if not genre:
        return render_template('filter_results.html', books=[], genre=genre, error="Please provide a genre.")

    # Filter books by genre
    filtered_books = books[books['categories'].str.contains(genre, case=False, na=False)]

    # If no books are found, handle the case
    if filtered_books.empty:
        return render_template('filter_results.html', books=[], genre=genre, error="No books found for the specified genre.")
    
    # Prepare the books data for rendering
    filtered_books = filtered_books[['title', 'authors', 'categories', 'thumbnail', 'average_rating']].copy()
    filtered_books['index'] = filtered_books.index
    filtered_books['thumbnail'] = filtered_books['thumbnail'].apply(
        lambda x: x if pd.notna(x) else 'static/images/none.JPG'
    )
    
    return render_template('filter_results.html', books=filtered_books.to_dict(orient='records'), genre=genre)


@app.route('/faqs', methods=['GET'])
def faqs():
    return render_template('faqs.html')





if __name__ == '__main__':
    app.run(debug=True)




