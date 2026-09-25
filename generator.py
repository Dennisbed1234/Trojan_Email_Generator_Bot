import csv
import json
import os
import random
import re
import tempfile
from pathlib import Path

FIRST_NAMES = [
    "amelia", "olivia", "emma", "ava", "sophia",
    "isabella", "mia", "charlotte", "luna", "harper",
    "evelyn", "camila", "gianna", "abigail", "ella",
    "noah", "liam", "elijah", "oliver", "james",
    "william", "benjamin", "lucas", "henry", "theodore",
    "jack", "levi", "alexander", "jackson", "mateo",
    "daniel", "michael", "mason", "sebastian", "ethan",
]

LAST_NAMES = [
    "smith", "johnson", "williams", "brown", "jones",
    "garcia", "miller", "davis", "rodriguez", "martinez",
    "hernandez", "lopez", "gonzalez", "wilson", "anderson",
    "thomas", "taylor", "moore", "jackson", "martin",
    "lee", "thompson", "white", "harris", "sanchez",
    "clark", "ramirez", "lewis", "robinson", "walker",
    "young", "allen", "king", "wright", "scott",
]


def sanitize(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "", value)
    return value


def make_email(first: str, last: str, number: int, domain: str) -> str:
    first = sanitize(first)
    last = sanitize(last)

    patterns = [
        f"{first}.{last}{number}@{domain}",
        f"{first}{last}{number}@{domain}",
        f"{first}_{last}{number}@{domain}",
        f"{first}{number}.{last}@{domain}",
    ]

    return random.choice(patterns)


def generate_emails(count: int, domain: str = "example.test"):
    """
    Generate synthetic emails without storing the entire dataset in RAM.
    """

    for number in range(1, count + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)

        yield make_email(
            first=first,
            last=last,
            number=number,
            domain=domain,
        )


def generate_file(
    count: int,
    output_format: str,
    domain: str = "example.test",
):
    """
    Creates a temporary output file and streams generated records into it.
    """

    suffix = {
        "txt": ".txt",
        "csv": ".csv",
        "json": ".json",
    }[output_format]

    fd, path = tempfile.mkstemp(
        prefix="synthetic_emails_",
        suffix=suffix,
    )

    os.close(fd)

    if output_format == "txt":
        with open(path, "w", encoding="utf-8") as file:
            for email in generate_emails(count, domain):
                file.write(email + "\n")

    elif output_format == "csv":
        with open(
            path,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:
            writer = csv.writer(file)
            writer.writerow(["email"])

            for email in generate_emails(count, domain):
                writer.writerow([email])

    elif output_format == "json":
        with open(path, "w", encoding="utf-8") as file:
            file.write("[\n")

            first = True

            for email in generate_emails(count, domain):
                if not first:
                    file.write(",\n")

                json.dump(email, file)
                first = False

            file.write("\n]\n")

    return path