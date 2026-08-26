from pathlib import Path
import sqlite3

from flask import Flask, render_template, request, redirect, url_for 

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database" / "sports.db"


def get_db_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def run_query(query, parameters=()):
    connection = get_db_connection()

    rows = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()
    return rows

def get_total(table_name):
    connection = get_db_connection()

    result = connection.execute(
        f"SELECT COUNT(*) AS total FROM {table_name}"
    ).fetchone()

    connection.close()
    return result["total"]

@app.route("/")
def home():
    return "Hello from Flask on Vercel!"
    totals = {
        "students": get_total("STUDENT"),
        "teams": get_total("TEAMS"),
        "members": get_total("TEAM_MEMBER"),
        "games": get_total("GAME"),
        "locations": get_total("LOCATION"),
        "sports": get_total("SPORT")
    }

    return render_template("index.html", totals=totals)

@app.route("/students")
def students():
    search_query = request.args.get("q", "").strip()

    if search_query:
        value = f"%{search_query}%"

        student_rows = run_query("""
            SELECT student_id, first_name, last_name, class
            FROM STUDENT
            WHERE student_id LIKE ?
               OR first_name LIKE ?
               OR last_name LIKE ?
               OR class LIKE ?
               OR (first_name || ' ' || last_name) LIKE ?
            ORDER BY last_name, first_name
        """, (value, value, value, value, value))

    else:
        student_rows = run_query("""
            SELECT student_id, first_name, last_name, class
            FROM STUDENT
            ORDER BY last_name, first_name
        """)

    return render_template(
        "students.html",
        students=student_rows,
        search_query=search_query
    )

@app.route("/teams")
def teams():

    team_rows = run_query("""
        SELECT team_id, team_name, sport_name
        FROM TEAMS
        ORDER BY team_name
    """)

    return render_template("teams.html", teams=team_rows)

@app.route("/team-members")
def team_members():
    search_query = request.args.get("q", "").strip()

    query = """
        SELECT
            TEAM_MEMBER.team_member_id,
            TEAMS.team_name,
            STUDENT.first_name,
            STUDENT.last_name,
            TEAM_MEMBER.role
        FROM TEAM_MEMBER
        JOIN TEAMS
            ON TEAM_MEMBER.team_id = TEAMS.team_id
        JOIN STUDENT
            ON TEAM_MEMBER.student_id = STUDENT.student_id
    """

    parameters = ()

    if search_query:
        value = f"%{search_query}%"

        query += """
            WHERE TEAM_MEMBER.team_member_id LIKE ?
               OR TEAMS.team_name LIKE ?
               OR STUDENT.first_name LIKE ?
               OR STUDENT.last_name LIKE ?
               OR (STUDENT.first_name || ' ' || STUDENT.last_name) LIKE ?
               OR TEAM_MEMBER.role LIKE ?
        """

        parameters = (
            value,
            value,
            value,
            value,
            value,
            value
        )

    query += """
        ORDER BY TEAMS.team_name, STUDENT.last_name
    """

    member_rows = run_query(query, parameters)

    return render_template(
        "team_member.html",
        members=member_rows,
        search_query=search_query
    )

@app.route("/games")
def games():

    game_rows = run_query("""
        SELECT
            GAME.game_id,
            TEAMS.team_name,
            LOCATION.location_name,
            GAME.date,
            GAME.time,
            GAME.team_score,
            GAME.opponent_score,
            GAME.final_result
        FROM GAME
        JOIN TEAMS
            ON GAME.team_id = TEAMS.team_id
        JOIN LOCATION
            ON GAME.location_id = LOCATION.location_id
        ORDER BY GAME.date, GAME.time
    """)

    return render_template("games.html", games=game_rows)

@app.route("/locations")
def locations():

    location_rows = run_query("""
        SELECT location_id, location_name
        FROM LOCATION
        ORDER BY location_name
    """)

    return render_template(
        "locations.html",
        locations=location_rows
    )

@app.route("/sports")
def sports():

    sport_rows = run_query("""
        SELECT sport_id, sport_name
        FROM SPORT
        ORDER BY sport_name
    """)

    return render_template("sports.html", sports=sport_rows)

@app.route("/search")
def search():

    search_term = request.args.get("search", "").strip()

    # If the user searches for a page/category,
    # It will send them directly to that page.
    category = search_term.lower()

    category_pages = {
        "student": "students",
        "students": "students",
        "player": "students",
        "players": "students",

        "team": "teams",
        "teams": "teams",

        "member": "team_members",
        "members": "team_members",
        "team member": "team_members",
        "team members": "team_members",

        "game": "games",
        "games": "games",

        "location": "locations",
        "locations": "locations",

        "sport": "sports",
        "sports": "sports"
    }

    if category in category_pages:
        return redirect(url_for(category_pages[category]))

    results = {
        "students": [],
        "teams": [],
        "members": [],
        "games": [],
        "locations": [],
        "sports": []
    }

    if search_term:
        value = f"%{search_term}%"

        results["students"] = run_query("""
            SELECT student_id, first_name, last_name, class
            FROM STUDENT
            WHERE student_id LIKE ?
               OR first_name LIKE ?
               OR last_name LIKE ?
               OR class LIKE ?
            ORDER BY last_name, first_name
        """, (value, value, value, value))

        results["teams"] = run_query("""
            SELECT team_id, team_name, sport_name
            FROM TEAMS
            WHERE team_id LIKE ?
               OR team_name LIKE ?
               OR sport_name LIKE ?
            ORDER BY team_name
        """, (value, value, value))

        results["members"] = run_query("""
            SELECT
                TEAM_MEMBER.team_member_id,
                TEAMS.team_name,
                STUDENT.first_name,
                STUDENT.last_name,
                TEAM_MEMBER.role
            FROM TEAM_MEMBER
            JOIN TEAMS
                ON TEAM_MEMBER.team_id = TEAMS.team_id
            JOIN STUDENT
                ON TEAM_MEMBER.student_id = STUDENT.student_id
            WHERE TEAM_MEMBER.team_member_id LIKE ?
               OR TEAMS.team_name LIKE ?
               OR STUDENT.first_name LIKE ?
               OR STUDENT.last_name LIKE ?
               OR TEAM_MEMBER.role LIKE ?
            ORDER BY TEAMS.team_name, STUDENT.last_name
        """, (value, value, value, value, value))

        results["games"] = run_query("""
            SELECT
                GAME.game_id,
                TEAMS.team_name,
                LOCATION.location_name,
                GAME.date,
                GAME.time,
                GAME.team_score,
                GAME.opponent_score,
                GAME.final_result
            FROM GAME
            JOIN TEAMS
                ON GAME.team_id = TEAMS.team_id
            JOIN LOCATION
                ON GAME.location_id = LOCATION.location_id
            WHERE GAME.game_id LIKE ?
               OR TEAMS.team_name LIKE ?
               OR LOCATION.location_name LIKE ?
               OR GAME.date LIKE ?
               OR GAME.time LIKE ?
               OR GAME.final_result LIKE ?
            ORDER BY GAME.date, GAME.time
        """, (
            value,
            value,
            value,
            value,
            value,
            value
        ))

        results["locations"] = run_query("""
            SELECT location_id, location_name
            FROM LOCATION
            WHERE location_id LIKE ?
               OR location_name LIKE ?
            ORDER BY location_name
        """, (value, value))

        results["sports"] = run_query("""
            SELECT sport_id, sport_name
            FROM SPORT
            WHERE sport_id LIKE ?
               OR sport_name LIKE ?
            ORDER BY sport_name
        """, (value, value))

    total_results = sum(
        len(group) for group in results.values()
    )

    return render_template(
        "search_results.html",
        search_term=search_term,
        results=results,
        total_results=total_results
    )



@app.errorhandler(404)
def page_not_found(error):
    return "<h1>404</h1><p>The requested page was not found.</p>", 404

if __name__ == "__main__":
    app.run(debug=True, port=5001)
