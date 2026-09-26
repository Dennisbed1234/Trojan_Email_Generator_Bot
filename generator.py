import csv
import json
import os
import random
import re
import tempfile


FIRST_NAMES = [
    "amelia", "olivia", "emma", "ava", "sophia", "isabella", "mia", "charlotte",
    "luna", "harper", "evelyn", "camila", "gianna", "abigail", "ella", "scarlett",
    "victoria", "aria", "grace", "chloe", "zoey", "riley", "lily", "layla",
    "lillian", "nora", "hazel", "lily", "violet", "aurora", "nova", "ellie",
    "ivy", "stella", "everleigh", "isla", "leah", "eliana", "paisley", "genesis",
    "naomi", "maya", "madeline", "elena", "caroline", "sarah", "alice", "nevaeh",
    "autumn", "quinn", "piper", "ruby", "samantha", "sadie", "delilah", "josephine",
    "claire", "peyton", "adeline", "emery", "anna", "iris", "emily", "lauren",
    "katherine", "maria", "savannah", "kennedy", "madelyn", "cora", "aaliyah",
    "julia", "arianа", "ximena", "kaylee", "sophie", "margaret", "reagan",
    "gianna", "valentina", "sydney", "eden", "jade", "brielle", "penny",
    "melanie", "vivian", "rachel", "everly", "riley", "naomi", "athena",
    "lucy", "kinsley", "bella", "mary", "clara", "hadley", "skylar", "jasmine",
    "josephine", "julia", "delaney", "molly", "reese", "londyn", "lucille",
    "paige", "mckenzie", "kayla", "alina", "blakely", "rose", "finley",
    "faith", "carter", "lola", "melody", "lyla", "poppy", "alana", "arabella",
    "brooke", "kayleigh", "daisy", "sloane", "june", "presley", "teagan",
    "adelyn", "raelynn", "alexa", "lila", "morgan", "jennifer", "rebecca",
    "angela", "ashley", "danielle", "nicole", "michelle", "amanda", "heather",
    "stephanie", "christine", "kimberly", "courtney", "brittany", "megan",
    "taylor", "jessica", "erica", "melissa", "amber", "rachel", "kelsey",
    "allison", "courtney", "kaitlyn", "alyssa", "brianna", "kayla", "kristen",
    "noah", "liam", "elijah", "oliver", "james", "william", "benjamin", "lucas",
    "henry", "theodore", "jack", "levi", "alexander", "jackson", "mateo", "daniel",
    "michael", "mason", "sebastian", "ethan", "logan", "owen", "samuel", "jacob",
    "asher", "aiden", "john", "joseph", "wyatt", "david", "leo", "luke",
    "julian", "hudson", "grayson", "matthew", "ezra", "gabriel", "carter",
    "isaac", "jayden", "luca", "anthony", "dylan", "lincoln", "thomas", "maverick",
    "elias", "joshua", "charles", "christopher", "ezekiel", "miles", "nathan",
    "caleb", "ryan", "nathaniel", "adrian", "christian", "muhammad", "cooper",
    "declan", "roman", "eastаn", "landon", "kai", "winston", "robert", "jameson",
    "axel", "ian", "everett", "greyson", "wesley", "jeremiah", "hunter",
    "leonardo", "jordan", "josiah", "jason", "vincent", "bennett", "silas",
    "brayden", "micah", "damian", "august", "kai", "emmett", "river", "ryder",
    "bryson", "gael", "felix", "jude", "beau", "parker", "brooks", "ryan",
    "cameron", "connor", "carson", "colton", "dominick", "xavier", "ashton",
    "braxton", "nolan", "eastоn", "blake", "maxwell", "malachi", "tristan",
    "lennox", "milo", "zachary", "preston", "jesse", "cole", "brandon", "brian",
    "kevin", "justin", "austin", "aaron", "tyler", "adam", "eric", "steven",
    "jason", "bryan", "sean", "patrick", "jared", "cody", "garrett", "derek",
    "trevor", "cameron", "chase", "spencer", "blake", "drew", "logan", "dalton",
    "grant", "jordan", "cory", "colin", "devin", "bradley", "calvin", "shane",
    "marcus", "andre", "terrence", "derrick", "marvin", "malcolm", "damon",
    "desmond", "reginald", "terrell", "rodney", "isaiah", "josue", "omar",
    "antonio", "manuel", "ricardo", "alejandro", "miguel", "javier", "carlos",
    "diego", "jorge", "eduardo", "fernando", "luis", "rafael", "gabriel",
]


LAST_NAMES = [
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis",
    "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson", "anderson",
    "thomas", "taylor", "moore", "jackson", "martin", "lee", "thompson", "white",
    "harris", "sanchez", "clark", "ramirez", "lewis", "robinson", "walker",
    "young", "allen", "king", "wright", "scott", "torres", "nguyen", "hill",
    "flores", "green", "adams", "nelson", "baker", "hall", "rivera", "campbell",
    "mitchell", "carter", "roberts", "gomez", "phillips", "evans", "turner",
    "diaz", "parker", "cruz", "edwards", "collins", "reyes", "stewart", "morris",
    "morales", "murphy", "cook", "rogers", "gutierrez", "ortiz", "morgan",
    "cooper", "peterson", "bailey", "reed", "kelly", "howard", "ramos", "kim",
    "cox", "ward", "richardson", "watson", "brooks", "chavez", "wood", "james",
    "bennett", "gray", "mendoza", "ruiz", "hughes", "price", "alvarez", "castillo",
    "sanders", "patel", "myers", "long", "ross", "foster", "jimenez", "powell",
    "jenkins", "perry", "russell", "sullivan", "bell", "coleman", "butler",
    "henderson", "barnes", "gonzales", "fisher", "vasquez", "simmons", "romero",
    "jordan", "patterson", "alexander", "hamilton", "graham", "reynolds", "griffin",
    "wallace", "moreno", "west", "cole", "hayes", "bryant", "herrera", "gibson",
    "ellis", "tran", "medina", "aguilar", "stevens", "murray", "ford", "castro",
    "marshall", "owens", "harrison", "fernandez", "mcdonald", "woods", "washington",
    "kennedy", "wells", "vargas", "henry", "chen", "freeman", "webb", "tucker",
    "guzman", "burns", "crawford", "olson", "simpson", "porter", "hunter",
    "gordon", "mendez", "silva", "shaw", "snyder", "mason", "dixon", "munoz",
    "hunt", "hicks", "holmes", "palmer", "wagner", "black", "robertson",
    "boyd", "rose", "stone", "salazar", "fox", "warren", "mills", "meyer",
    "rice", "schmidt", "garza", "daniels", "ferguson", "nichols", "stephens",
    "soto", "weaver", "ryan", "gardner", "payne", "grant", "dunn", "kelley",
    "spencer", "hawkins", "arnold", "pierce", "vazquez", "hansen", "peters",
    "santos", "hart", "bradley", "knight", "elliott", "cunningham", "duncan",
    "armstrong", "hudson", "carroll", "lane", "riley", "andrews", "alvarado",
    "ray", "delgado", "berry", "perry", "johnston", "matthews", "casey",
    "mccarthy", "mcdaniel", "singh", "compton", "richard", "willis", "williams",
    "carpenter", "lawrence", "sandoval", "guerrero", "george", "chapman",
    "rivers", "alston", "benson", "bowers", "burke", "burton", "caldwell",
    "chandler", "conley", "conway", "craig", "cross", "curry", "davenport",
    "dawson", "decker", "dennis", "donaldson", "douglas", "drake", "dudley",
    "duffy", "dunlap", "durham", "eaton", "english", "erickson", "farley",
    "farmer", "farnsworth", "finley", "fleming", "floyd", "foreman", "fowler",
    "francis", "franklin", "frazier", "gallegos", "gallagher", "garner",
    "garrison", "gentry", "gilbert", "gillespie", "glass", "glover", "goodman",
    "goodwin", "graves", "greer", "grimes", "gross", "guerra", "guthrie",
    "hahn", "hale", "hancock", "hardin", "hardy", "harper", "harrington",
    "hartman", "harvey", "hatch", "hatfield", "hathaway", "hays", "heath",
    "hendrix", "henson", "higgins", "hines", "hinton", "hoover", "hopkins",
    "horn", "horton", "houston", "howe", "hubbard", "hubbard", "humphrey",
    "hutchinson", "ingram", "irwin", "iverson", "jacobs", "jefferson", "jennings",
    "jensen", "jewell", "joyce", "kane", "kaufman", "keith", "keller",
    "kemp", "kerr", "key", "kidd", "kinney", "kirby", "kirk", "kline",
    "knapp", "lambert", "lambert", "lancaster", "larson", "lawson", "leach",
    "leonard", "lindsey", "little", "livingston", "logan", "lovell", "lucas",
    "lyons", "maldonado", "malone", "mansfield", "marsh", "martins", "mathews",
    "maxwell", "may", "mayer", "mccall", "mccarty", "mcdowell", "mcgee",
    "mckay", "mckee", "mckenzie", "mclean", "mclean", "mcmahon", "mcneil",
    "meadows", "melton", "meyers", "middleton", "milton", "miranda", "monroe",
]

DOMAINS = [
    "gmail.com",
    "gmail.com",
    "gmail.com",
    "yahoomail.com",
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

    number = random_digits(1, 4)

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
            f"{random_digits(1, 4)}"
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