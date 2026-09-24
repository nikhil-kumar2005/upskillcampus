"""
Library Management System
--------------------------
A console-based Library Management System built in Python.

Features:
1. Add / Remove / Update / Search Books
2. Register / Remove Members
3. Issue Books to Members
4. Return Books
5. View all Books and Members
6. Persistent storage using JSON files (books.json, members.json)

Author: Khilen Raj
"""

import json
import os
from datetime import datetime, timedelta

BOOKS_FILE = "books.json"
MEMBERS_FILE = "members.json"
LOAN_PERIOD_DAYS = 14


# ---------------------------------------------------------------------------
# Data persistence helpers
# ---------------------------------------------------------------------------
def load_data(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return {}


def save_data(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


# ---------------------------------------------------------------------------
# Book class
# ---------------------------------------------------------------------------
class Book:
    def __init__(self, book_id, title, author, copies):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.copies = copies          # total copies owned by library
        self.available = copies       # copies currently available

    def to_dict(self):
        return {
            "book_id": self.book_id,
            "title": self.title,
            "author": self.author,
            "copies": self.copies,
            "available": self.available,
        }

    @staticmethod
    def from_dict(d):
        b = Book(d["book_id"], d["title"], d["author"], d["copies"])
        b.available = d["available"]
        return b


# ---------------------------------------------------------------------------
# Member class
# ---------------------------------------------------------------------------
class Member:
    def __init__(self, member_id, name, email):
        self.member_id = member_id
        self.name = name
        self.email = email
        self.borrowed_books = {}   # book_id -> due_date (str)

    def to_dict(self):
        return {
            "member_id": self.member_id,
            "name": self.name,
            "email": self.email,
            "borrowed_books": self.borrowed_books,
        }

    @staticmethod
    def from_dict(d):
        m = Member(d["member_id"], d["name"], d["email"])
        m.borrowed_books = d.get("borrowed_books", {})
        return m


# ---------------------------------------------------------------------------
# Library class - the core system
# ---------------------------------------------------------------------------
class Library:
    def __init__(self):
        self.books = {}
        self.members = {}
        self._load()

    def _load(self):
        raw_books = load_data(BOOKS_FILE)
        raw_members = load_data(MEMBERS_FILE)
        self.books = {k: Book.from_dict(v) for k, v in raw_books.items()}
        self.members = {k: Member.from_dict(v) for k, v in raw_members.items()}

    def _save(self):
        save_data(BOOKS_FILE, {k: v.to_dict() for k, v in self.books.items()})
        save_data(MEMBERS_FILE, {k: v.to_dict() for k, v in self.members.items()})

    # ---------------- Book operations ----------------
    def add_book(self, book_id, title, author, copies):
        if book_id in self.books:
            print(f"[!] Book ID {book_id} already exists.")
            return
        self.books[book_id] = Book(book_id, title, author, copies)
        self._save()
        print(f"[+] Book '{title}' added successfully.")

    def remove_book(self, book_id):
        if book_id in self.books:
            del self.books[book_id]
            self._save()
            print(f"[-] Book {book_id} removed.")
        else:
            print("[!] Book not found.")

    def search_book(self, keyword):
        results = [
            b for b in self.books.values()
            if keyword.lower() in b.title.lower() or keyword.lower() in b.author.lower()
        ]
        if results:
            for b in results:
                print(f"  {b.book_id}: {b.title} by {b.author} "
                      f"(Available: {b.available}/{b.copies})")
        else:
            print("[!] No matching books found.")
        return results

    def list_books(self):
        if not self.books:
            print("[!] No books in the library.")
            return
        print(f"{'ID':<6}{'Title':<25}{'Author':<20}{'Available':<10}")
        print("-" * 61)
        for b in self.books.values():
            print(f"{b.book_id:<6}{b.title:<25}{b.author:<20}{b.available}/{b.copies}")

    # ---------------- Member operations ----------------
    def add_member(self, member_id, name, email):
        if member_id in self.members:
            print(f"[!] Member ID {member_id} already exists.")
            return
        self.members[member_id] = Member(member_id, name, email)
        self._save()
        print(f"[+] Member '{name}' registered successfully.")

    def remove_member(self, member_id):
        if member_id in self.members:
            del self.members[member_id]
            self._save()
            print(f"[-] Member {member_id} removed.")
        else:
            print("[!] Member not found.")

    def list_members(self):
        if not self.members:
            print("[!] No members registered.")
            return
        for m in self.members.values():
            borrowed = ", ".join(m.borrowed_books.keys()) if m.borrowed_books else "None"
            print(f"  {m.member_id}: {m.name} ({m.email}) | Borrowed: {borrowed}")

    # ---------------- Issue / Return operations ----------------
    def issue_book(self, book_id, member_id):
        book = self.books.get(book_id)
        member = self.members.get(member_id)

        if not book:
            print("[!] Book not found.")
            return
        if not member:
            print("[!] Member not found.")
            return
        if book.available <= 0:
            print(f"[!] '{book.title}' is currently out of stock.")
            return
        if book_id in member.borrowed_books:
            print(f"[!] {member.name} has already borrowed this book.")
            return

        due_date = (datetime.now() + timedelta(days=LOAN_PERIOD_DAYS)).strftime("%Y-%m-%d")
        member.borrowed_books[book_id] = due_date
        book.available -= 1
        self._save()
        print(f"[+] '{book.title}' issued to {member.name}. Due date: {due_date}")

    def return_book(self, book_id, member_id):
        book = self.books.get(book_id)
        member = self.members.get(member_id)

        if not book or not member:
            print("[!] Invalid book or member ID.")
            return
        if book_id not in member.borrowed_books:
            print(f"[!] {member.name} did not borrow this book.")
            return

        due_date_str = member.borrowed_books.pop(book_id)
        book.available += 1
        self._save()

        due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
        if datetime.now() > due_date:
            days_late = (datetime.now() - due_date).days
            fine = days_late * 5   # Rs. 5 per day fine
            print(f"[+] '{book.title}' returned late by {days_late} day(s). Fine: Rs.{fine}")
        else:
            print(f"[+] '{book.title}' returned successfully. Thank you!")


# ---------------------------------------------------------------------------
# Console Menu (CLI)
# ---------------------------------------------------------------------------
def main():
    lib = Library()

    menu = """
========= LIBRARY MANAGEMENT SYSTEM =========
1. Add Book
2. Remove Book
3. Search Book
4. List All Books
5. Register Member
6. Remove Member
7. List All Members
8. Issue Book
9. Return Book
0. Exit
==============================================
"""
    while True:
        print(menu)
        choice = input("Enter your choice: ").strip()

        if choice == "1":
            bid = input("Book ID: ").strip()
            title = input("Title: ").strip()
            author = input("Author: ").strip()
            copies = int(input("Number of copies: ").strip())
            lib.add_book(bid, title, author, copies)

        elif choice == "2":
            bid = input("Book ID to remove: ").strip()
            lib.remove_book(bid)

        elif choice == "3":
            keyword = input("Enter title/author keyword: ").strip()
            lib.search_book(keyword)

        elif choice == "4":
            lib.list_books()

        elif choice == "5":
            mid = input("Member ID: ").strip()
            name = input("Name: ").strip()
            email = input("Email: ").strip()
            lib.add_member(mid, name, email)

        elif choice == "6":
            mid = input("Member ID to remove: ").strip()
            lib.remove_member(mid)

        elif choice == "7":
            lib.list_members()

        elif choice == "8":
            bid = input("Book ID: ").strip()
            mid = input("Member ID: ").strip()
            lib.issue_book(bid, mid)

        elif choice == "9":
            bid = input("Book ID: ").strip()
            mid = input("Member ID: ").strip()
            lib.return_book(bid, mid)

        elif choice == "0":
            print("Exiting Library Management System. Goodbye!")
            break

        else:
            print("[!] Invalid choice, please try again.")


if __name__ == "__main__":
    main()
