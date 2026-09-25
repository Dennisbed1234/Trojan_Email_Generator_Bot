import csv
import json
import os
import random
import re
import tempfile


FIRST_NAMES = [
    "amelia", "olivia", "emma", "ava", "sophia",
    "isabella", "mia", "charlotte", "luna", "harper",
    "evelyn", "camila", "gianna", "abigail", "ella",
    "scarlett", "victoria", "aria", "grace", "chloe",
    "noah", "liam", "elijah", "oliver", "james",
    "william", "benjamin", "lucas", "henry", "theodore",
    "jack", "levi", "alexander", "jackson", "mateo",
    "daniel", "michael", "mason", "sebastian", "ethan",
    "logan", "owen", "samuel", "jacob", "asher",
]


LAST_NAMES = [
    "smith", "johnson", "williams", "brown", "jones",
    "garcia", "miller", "davis", "rodriguez", "martinez",
    "hernandez", "lopez", "gonzalez", "wilson", "anderson",
    "thomas", "taylor", "moore", "jackson", "martin",
    "lee", "thompson", "white", "harris", "sanchez",
    "clark", "ramirez", "lewis", "robinson", "walker",
    "young", "allen", "king", "wright", "scott",
    "torres", "nguyen", "hill", "flores", "green",
    "adams", "nelson", "baker", "hall", "rivera",
]


DOMAINS = [
    "gmail.com",
    "yahoomail.com",
    "aol.com",
    "hotmail.com",
    "outlook.com",
]


def random_case(text):
    styles = [
        str.lower,
        str.upper,
        str.capitalize,
        lambda value: "".join(
            char.upper()
            if random.choice([True, False])
            else char.lower()
            for char in value
        ),
    ]

    return random.choice(styles)(text)


def random_digits(
    min_length=2,
    max_length=7,
):
    length = random.randint(
        min_length,
        max_length,
    )

    return "".join(
        random.choice(
            "0123456789"
        )
        for _ in range(length)
    )


def random_letters(
    min_length=1,
    max_length=4,
):
    length = random.randint(
        min_length,
        max_length,
    )

    return "".join(
        random.choice(
            "abcdefghijklmnopqrstuvwxyz"
        )
        for _ in range(length)
    )


def sanitize(value):
    return re.sub(
        r"[^a-zA-Z0-9]",
        "",
        value,
    )


def create_local_part():

    first = sanitize(
        random_case(
            random.choice(
                FIRST_NAMES
            )
        )
    )

    last = sanitize(
        random_case(
            random.choice(
                LAST_NAMES
            )
        )
    )

    number = random_digits()

    extra_letters = random_letters()

    separator = random.choice(
        [
            ".",
            "_",
            "-",
            "",
        ]
    )

    pattern = random.randint(
        1,
        12,
    )

    if pattern == 1:
        local = (
            f"{first}"
            f"{separator}"
            f"{last}"
        )

    elif pattern == 2:
        local = (
            f"{first}"
            f"{separator}"
            f"{last}"
            f"{number}"
        )

    elif pattern == 3:
        local = (
            f"{first}"
            f"{number}"
            f"{separator}"
            f"{last}"
        )

    elif pattern == 4:
        local = (
            f"{first}"
            f"{separator}"
            f"{number}"
            f"{last}"
        )

    elif pattern == 5:
        local = (
            f"{first}"
            f"{extra_letters}"
            f"{separator}"
            f"{last}"
        )

    elif pattern == 6:
        local = (
            f"{first}"
            f"{separator}"
            f"{last}"
            f"{extra_letters}"
        )

    elif pattern == 7:
        local = (
            f"{extra_letters}"
            f"{separator}"
            f"{first}"
            f"{last}"
            f"{number}"
        )

    elif pattern == 8:
        local = (
            f"{first}"
            f"{number}"
            f"{extra_letters}"
        )

    elif pattern == 9:
        local = (
            f"{first}"
            f"{separator}"
            f"{last}"
            f"{number}"
            f"{extra_letters}"
        )

    elif pattern == 10:
        local = (
            f"{first}"
            f"{number}"
            f"{separator}"
            f"{last}"
            f"{extra_letters}"
        )

    elif pattern == 11:
        local = (
            f"{extra_letters}"
            f"{first}"
            f"{separator}"
            f"{last}"
            f"{number}"
        )

    else:
        local = (
            f"{first}"
            f"{separator}"
            f"{last}"
            f"{random_digits(1, 10)}"
        )

    local = local.strip(
        "._-"
    )

    local = re.sub(
        r"[._-]{2,}",
        lambda match: match.group(0)[0],
        local,
    )

    return local


def create_email():
    return (
        f"{create_local_part()}"
        f"@{random.choice(DOMAINS)}"
    )


def generate_emails(count):

    seen = set()

    while len(seen) < count:

        email = create_email()

        if email in seen:
            continue

        seen.add(email)

        yield email


def generate_file(
    count,
    output_format,
):

    if output_format not in {
        "txt",
        "csv",
        "json",
    }:
        raise ValueError(
            "Unsupported output format."
        )

    suffix = {
        "txt": ".txt",
        "csv": ".csv",
        "json": ".json",
    }[output_format]

    fd, path = tempfile.mkstemp(
        prefix="valid_emails_",
        suffix=suffix,
    )

    os.close(fd)

    if output_format == "txt":

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:

            for email in generate_emails(
                count
            ):
                file.write(email)
                file.write("\n")

    elif output_format == "csv":

        with open(
            path,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.writer(file)

            writer.writerow(
                ["email"]
            )

            for email in generate_emails(
                count
            ):
                writer.writerow(
                    [email]
                )

    elif output_format == "json":

        with open(
            path,
            "w",
            encoding="utf-8",
        ) as file:

            file.write("[\n")

            first = True

            for email in generate_emails(
                count
            ):

                if not first:
                    file.write(",\n")

                json.dump(
                    email,
                    file,
                    ensure_ascii=False,
                )

                first = False

            file.write("\n]\n")

    return path