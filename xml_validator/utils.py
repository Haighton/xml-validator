# xml_validator/utils.py
import csv


def write_csv_log(rows, csv_log_filename):
    fieldnames = ["batch", "file", "validation_type", "status", "details"]
    file_exists = csv_log_filename.exists()

    with csv_log_filename.open("a", encoding="utf-8", newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)
