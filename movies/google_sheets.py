import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

class GoogleSheetsHandler:
    def __init__(self, creds_file, spreadsheet_id):
        self.scope = ["https://spreadsheets.google.com/feeds",
                      "https://www.googleapis.com/auth/spreadsheets",
                      "https://www.googleapis.com/auth/drive.file",
                      "https://www.googleapis.com/auth/drive"]
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, self.scope)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_key(spreadsheet_id)

    def clear_and_reset_sheet(self, worksheet_name, headers):
        worksheet = self.sheet.worksheet(worksheet_name)
        worksheet.clear()  # Очищаем все данные
        worksheet.append_row(headers)  # Добавляем заголовки

    def save_movies_data(self, movies_file_path):
        worksheet_name = "Movies Data"
        headers = [
            "Position in rating",
            "Title",
            "Original title",
            "Year",
            "Rating",
            "Director(s)",
            "Cast"
        ]
        self.clear_and_reset_sheet(worksheet_name, headers)

        worksheet = self.sheet.worksheet(worksheet_name)

        with open(movies_file_path, 'r', encoding='utf-8') as f:
            movies_data = json.load(f)

        rows = []
        for movie in movies_data:
            row = [
                movie.get("Position in rating", ""),
                movie.get("Title", ""),
                movie.get("Original title", ""),
                movie.get("Year", ""),
                movie.get("Rating", ""),
                ", ".join(movie.get("Director(s)", [])),
                ", ".join(movie.get("Cast", [])),
            ]
            rows.append(row)

        if rows:
            worksheet.append_rows(rows)  # Пакетная запись данных

    def save_actor_analysis(self, actors_file_path):
        worksheet_name = "Actor Analysis"
        headers = [
            "Actor",
            "Movies Count",
            "Average Rating",
            "Movies"
        ]
        self.clear_and_reset_sheet(worksheet_name, headers)

        with open(actors_file_path, 'r', encoding='utf-8') as f:
            actors = json.load(f)

        worksheet = self.sheet.worksheet(worksheet_name)
        rows = []
        for actor_data in actors:
            row = [
                actor_data.get("Actor", ""),
                actor_data.get("Movies Count", ""),
                actor_data.get("Average Rating", ""),
                ", ".join(actor_data.get("Movies", [])),
            ]
            rows.append(row)

        if rows:
            worksheet.append_rows(rows)  # Пакетная запись данных
