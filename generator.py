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
    "lillian", "nora", "hazel", "violet", "aurora", "nova", "ellie", "ivy",
    "stella", "everleigh", "isla", "leah", "eliana", "paisley", "genesis",
    "naomi", "maya", "madeline", "elena", "caroline", "sarah", "alice", "nevaeh",
    "autumn", "quinn", "piper", "ruby", "samantha", "sadie", "delilah",
    "josephine", "claire", "peyton", "adeline", "emery", "anna", "iris", "emily",
    "lauren", "katherine", "maria", "savannah", "kennedy", "madelyn", "cora",
    "aaliyah", "julia", "ariana", "ximena", "kaylee", "sophie", "margaret",
    "reagan", "valentina", "sydney", "eden", "jade", "brielle", "penny",
    "melanie", "vivian", "rachel", "everly", "athena", "lucy", "kinsley", "bella",
    "mary", "clara", "hadley", "skylar", "jasmine", "delaney", "molly", "reese",
    "londyn", "lucille", "paige", "mckenzie", "kayla", "alina", "blakely", "rose",
    "finley", "faith", "carter", "lola", "melody", "lyla", "poppy", "alana",
    "arabella", "brooke", "kayleigh", "daisy", "sloane", "june", "presley",
    "teagan", "adelyn", "raelynn", "alexa", "lila", "morgan", "jennifer",
    "rebecca", "angela", "ashley", "danielle", "nicole", "michelle", "amanda",
    "heather", "stephanie", "christine", "kimberly", "courtney", "brittany",
    "megan", "taylor", "jessica", "erica", "melissa", "amber", "kelsey",
    "allison", "kaitlyn", "alyssa", "brianna", "kristen", "aaron", "abraham",
    "addison", "adriana", "alaina", "alanna", "alessandra", "alexandra", "alexis",
    "alicia", "alison", "alyson", "andrea", "angel", "angelica", "annabelle",
    "ariel", "ashlyn", "aubrey", "audrey", "avery", "bailey", "beckett", "belle",
    "briana", "bridget", "brooklyn", "callie", "caitlin", "caitlyn", "camille",
    "carly", "cassidy", "catherine", "cecilia", "charlie", "chelsea", "christina",
    "dakota", "dana", "daphne", "darlene", "diana", "donna", "dorothy", "elise",
    "elizabeth", "elsie", "emerson", "erin", "esther", "eva", "fiona", "frances",
    "gabriella", "gemma", "genevieve", "georgia", "gillian", "gina", "gloria",
    "gwendolyn", "hailey", "hannah", "harley", "harmony", "holly", "hope",
    "isabel", "isabelle", "jackie", "jacqueline", "jillian", "joanna", "jocelyn",
    "joy", "judith", "julie", "juliette", "kara", "karina", "karen", "katie",
    "kristina", "lacey", "lana", "laura", "leila", "leslie", "lindsey", "lindsay",
    "lizbeth", "lori", "lorraine", "lucia", "lydia", "mackenzie", "madison",
    "maggie", "makayla", "mallory", "mandy", "marissa", "marley", "mila",
    "miranda", "monica", "nancy", "natalie", "natalia", "nataly", "nina", "norah",
    "payton", "phoebe", "priscilla", "raven", "regina", "rosalie", "sabrina",
    "sandra", "sara", "selena", "serena", "sierra", "shelby", "sienna", "summer",
    "susan", "tiffany", "trinity", "valerie", "vanessa", "veronica", "wendy",
    "whitney", "willow", "zoe", "abby", "adele", "adrienne", "agnes", "aimee",
    "alexandria", "alyse", "amelie", "amy", "alba", "anastasia", "angelina",
    "anita", "annette", "annie", "april", "arielle", "ariella", "ashleigh",
    "amparo", "ashlee", "aspen", "aurelia", "bethany", "betty", "beverly",
    "bianca", "blythe", "bonnie", "ana", "brenda", "brenna", "bree", "brooklynn",
    "bryn", "camryn", "candace", "carla", "carol", "beatriz", "carolyn", "carrie",
    "cassandra", "cassie", "celeste", "charity", "charlene", "cheryl", "christy",
    "carmen", "cindy", "clarissa", "colleen", "connie", "constance", "corinne",
    "crystal", "cynthia", "dahlia", "catalina", "dawn", "deanna", "debbie",
    "deborah", "denise", "desiree", "diane", "dixie", "dominique", "consuelo",
    "dora", "doris", "edith", "eileen", "elaine", "eleanor", "ellen", "ellery",
    "eloise", "dolores", "elsa", "emmy", "esme", "estelle", "ethel", "eunice",
    "felicity", "florence", "gabrielle", "esperanza", "gail", "gertrude",
    "gladys", "greta", "gracie", "gretchen", "haley", "hattie", "helen", "estela",
    "henrietta", "hillary", "imogen", "ingrid", "irene", "jaime", "jamie", "jana",
    "janet", "gabriela", "janice", "jayla", "jean", "jeanette", "jenna", "jenny",
    "jessie", "jill", "joan", "guadalupe", "joanne", "jolene", "josie", "juliana",
    "juniper", "kacey", "kailey", "kali", "kate", "ines", "kathleen", "kathryn",
    "kathy", "katrina", "kay", "keira", "kendra", "kelli", "kerry", "juana",
    "kiara", "kirsten", "krista", "krystal", "lacy", "laila", "lainey", "lara",
    "larissa", "leticia", "laurel", "lena", "leona", "lexi", "liliana", "linda",
    "lisa", "lois", "louisa", "lorena", "lucinda", "lynn", "mabel", "macy",
    "maeve", "marcia", "margo", "marguerite", "marian", "lourdes", "marianne",
    "marilyn", "marina", "marjorie", "marlene", "marsha", "martha", "maureen",
    "mavis", "marisol", "maxine", "meadow", "meg", "meredith", "mikayla",
    "mildred", "mindy", "miriam", "misty", "marta", "mollie", "myra", "nadia",
    "nellie", "nia", "nikki", "noelle", "odette", "olive", "mercedes", "opal",
    "pamela", "patricia", "patsy", "pearl", "peggy", "penelope", "petra",
    "phyllis", "paloma", "polly",

    "noah", "liam", "elijah", "oliver", "james", "william", "benjamin", "lucas",
    "henry", "theodore", "jack", "levi", "alexander", "jackson", "mateo",
    "daniel", "michael", "mason", "sebastian", "ethan", "logan", "owen", "samuel",
    "jacob", "asher", "aiden", "john", "joseph", "wyatt", "david", "leo", "luke",
    "julian", "hudson", "grayson", "matthew", "ezra", "gabriel", "isaac",
    "jayden", "luca", "anthony", "dylan", "lincoln", "thomas", "maverick",
    "elias", "joshua", "charles", "christopher", "ezekiel", "miles", "nathan",
    "caleb", "ryan", "nathaniel", "adrian", "christian", "cooper", "declan",
    "roman", "easton", "landon", "kai", "winston", "robert", "jameson", "axel",
    "ian", "everett", "greyson", "wesley", "jeremiah", "hunter", "leonardo",
    "jordan", "josiah", "jason", "vincent", "bennett", "silas", "brayden",
    "micah", "damian", "august", "emmett", "river", "ryder", "bryson", "gael",
    "felix", "jude", "beau", "parker", "brooks", "cameron", "connor", "carson",
    "colton", "dominick", "xavier", "ashton", "braxton", "nolan", "blake",
    "maxwell", "malachi", "tristan", "lennox", "milo", "zachary", "preston",
    "jesse", "cole", "brandon", "brian", "kevin", "justin", "austin", "tyler",
    "adam", "eric", "steven", "bryan", "sean", "patrick", "jared", "cody",
    "garrett", "derek", "trevor", "chase", "spencer", "drew", "dalton", "grant",
    "cory", "colin", "devin", "bradley", "calvin", "shane", "marcus", "andre",
    "terrence", "derrick", "marvin", "malcolm", "damon", "desmond", "reginald",
    "terrell", "rodney", "isaiah", "josue", "omar", "antonio", "manuel",
    "ricardo", "alejandro", "miguel", "javier", "carlos", "diego", "jorge",
    "eduardo", "fernando", "luis", "rafael", "alex", "andrew", "andy", "arthur",
    "ben", "brendan", "brent", "bruce", "bryce", "carl", "chris", "clayton",
    "clifford", "clinton", "corey", "craig", "damien", "danny", "darren",
    "darryl", "davis", "dean", "donald", "douglas", "dustin", "edgar", "edward",
    "edwin", "elliot", "elliott", "emmanuel", "erik", "evan", "frank",
    "frederick", "gary", "gavin", "george", "gerald", "gerard", "gilbert",
    "glenn", "gregory", "griffin", "harold", "harrison", "harry", "hayden",
    "hector", "howard", "ivan", "jake", "jeffrey", "jeremy", "jimmy", "joel",
    "jonathan", "jonah", "jonas", "juan", "kaden", "kaleb", "kane", "keith",
    "kenneth", "kyle", "lawrence", "lee", "leon", "leonard", "lorenzo", "louie",
    "louis", "maddox", "mario", "marlon", "martin", "max", "maximus", "mitchell",
    "nicholas", "nick", "noel", "oscar", "paul", "peter", "philip", "raymond",
    "reid", "rhett", "richard", "roger", "ronald", "russell", "sam", "scott",
    "seth", "shawn", "stephen", "stuart", "tanner", "terry", "timothy", "toby",
    "tom", "tommy", "tony", "travis", "trey", "troy", "tucker", "victor",
    "walter", "wayne", "weston", "wiley", "will", "ace", "adler", "albert",
    "alden", "alfred", "allan", "allen", "alton", "ambrose", "alberto", "amos",
    "angus", "archer", "archie", "arlo", "arnold", "ashby", "atlas", "barrett",
    "alfonso", "barry", "bart", "beckham", "benedict", "benny", "bernard", "bert",
    "bill", "billy", "andres", "blaine", "bobby", "boyd", "brad", "braden",
    "bradford", "brady", "brantley", "brett", "arturo", "brice", "bronson",
    "brody", "bruno", "bryant", "buck", "burt", "byron", "cade", "benito",
    "caden", "cain", "callum", "camden", "carey", "carlton", "cecil", "cedric",
    "chad", "camilo", "chandler", "chester", "chip", "clarence", "claude", "clay",
    "clyde", "colby", "coleman", "domingo", "conrad", "corbin", "cornelius",
    "curtis", "dale", "dallas", "dan", "darrell", "darius", "emilio", "dave",
    "dax", "dennis", "denver", "dexter", "dillon", "dirk", "dominic", "don",
    "enrique", "doug", "doyle", "duane", "dudley", "duke", "dwight", "dwayne",
    "earl", "ed", "esteban", "eddie", "eli", "elmer", "emil", "enoch", "ernest",
    "ernie", "errol", "eugene", "federico", "fletcher", "floyd", "forrest",
    "francis", "franklin", "fred", "freddie", "gage", "gareth", "felipe", "gene",
    "geoffrey", "gideon", "gordon", "graham", "grady", "graeme", "gus", "guy",
    "francisco", "hal", "hank", "harlan", "harvey", "heath", "herbert", "herman",
    "homer", "hugh", "gonzalo", "jace", "jagger", "jamal", "jasper", "jay",
    "jayce", "jed", "jeff", "jerome", "guillermo", "jerry", "jett", "jim", "joe",
    "joey", "johnny", "jon", "judd", "jules", "gustavo", "junior", "karl",
    "kasen", "kellen", "kelvin", "kent", "kip", "kirk", "knox", "hugo", "kurt",
    "lamar", "lance", "larry", "lars", "lawson", "leland", "lenny", "leroy",
    "ignacio", "lester", "lewis", "lloyd", "lonnie", "loren", "lou", "lowell",
    "luther", "lyle", "isidro", "mack", "marc", "marshall", "marty", "mathew",
    "mick", "mike", "mikey", "milton", "jesus", "monty", "morris", "murphy",
    "ned", "neil", "nelson", "nico", "nigel", "norman", "joaquin", "otis",
]


LAST_NAMES = [
    "smith", "johnson", "williams", "brown", "jones", "garcia", "miller", "davis",
    "rodriguez", "martinez", "hernandez", "lopez", "gonzalez", "wilson",
    "anderson", "thomas", "taylor", "moore", "jackson", "martin", "lee",
    "thompson", "white", "harris", "sanchez", "clark", "ramirez", "lewis",
    "robinson", "walker", "young", "allen", "king", "wright", "scott", "torres",
    "nguyen", "hill", "flores", "green", "adams", "nelson", "baker", "hall",
    "rivera", "campbell", "mitchell", "carter", "roberts", "gomez", "phillips",
    "evans", "turner", "diaz", "parker", "cruz", "edwards", "collins", "reyes",
    "stewart", "morris", "morales", "murphy", "cook", "rogers", "gutierrez",
    "ortiz", "morgan", "cooper", "peterson", "bailey", "reed", "kelly", "howard",
    "ramos", "kim", "cox", "ward", "richardson", "watson", "brooks", "chavez",
    "wood", "james", "bennett", "gray", "mendoza", "ruiz", "hughes", "price",
    "alvarez", "castillo", "sanders", "patel", "myers", "long", "ross", "foster",
    "jimenez", "powell", "jenkins", "perry", "russell", "sullivan", "bell",
    "coleman", "butler", "henderson", "barnes", "gonzales", "fisher", "vasquez",
    "simmons", "romero", "jordan", "patterson", "alexander", "hamilton", "graham",
    "reynolds", "griffin", "wallace", "moreno", "west", "cole", "hayes", "bryant",
    "herrera", "gibson", "ellis", "tran", "medina", "aguilar", "stevens",
    "murray", "ford", "castro", "marshall", "owens", "harrison", "fernandez",
    "mcdonald", "woods", "washington", "kennedy", "wells", "vargas", "henry",
    "chen", "freeman", "webb", "tucker", "guzman", "burns", "crawford", "olson",
    "simpson", "porter", "hunter", "gordon", "mendez", "silva", "shaw", "snyder",
    "mason", "dixon", "munoz", "hunt", "hicks", "holmes", "palmer", "wagner",
    "black", "robertson", "boyd", "rose", "stone", "salazar", "fox", "warren",
    "mills", "meyer", "rice", "schmidt", "garza", "daniels", "ferguson",
    "nichols", "stephens", "soto", "weaver", "ryan", "gardner", "payne", "grant",
    "dunn", "kelley", "spencer", "hawkins", "arnold", "pierce", "vazquez",
    "hansen", "peters", "santos", "hart", "bradley", "knight", "elliott",
    "cunningham", "duncan", "armstrong", "hudson", "carroll", "lane", "riley",
    "andrews", "alvarado", "ray", "delgado", "berry", "johnston", "matthews",
    "casey", "mccarthy", "mcdaniel", "singh", "compton", "richard", "willis",
    "carpenter", "lawrence", "sandoval", "guerrero", "george", "chapman",
    "rivers", "alston", "benson", "bowers", "burke", "burton", "caldwell",
    "chandler", "conley", "conway", "craig", "cross", "curry", "davenport",
    "dawson", "decker", "dennis", "donaldson", "douglas", "drake", "dudley",
    "duffy", "dunlap", "durham", "eaton", "english", "erickson", "farley",
    "farmer", "farnsworth", "finley", "fleming", "floyd", "foreman", "fowler",
    "francis", "franklin", "frazier", "gallegos", "gallagher", "garner",
    "garrison", "gentry", "gilbert", "gillespie", "glass", "glover", "goodman",
    "goodwin", "graves", "greer", "grimes", "gross", "guerra", "guthrie", "hahn",
    "hale", "hancock", "hardin", "hardy", "harper", "harrington", "hartman",
    "harvey", "hatch", "hatfield", "hathaway", "hays", "heath", "hendrix",
    "henson", "higgins", "hines", "hinton", "hoover", "hopkins", "horn", "horton",
    "houston", "howe", "hubbard", "humphrey", "hutchinson", "ingram", "irwin",
    "iverson", "jacobs", "jefferson", "jennings", "jensen", "jewell", "joyce",
    "kane", "kaufman", "keith", "keller", "kemp", "kerr", "key", "kidd", "kinney",
    "kirby", "kirk", "kline", "knapp", "lambert", "lancaster", "larson", "lawson",
    "leach", "leonard", "lindsey", "little", "livingston", "logan", "lovell",
    "lucas", "lyons", "maldonado", "malone", "mansfield", "marsh", "martins",
    "mathews", "maxwell", "may", "mayer", "mccall", "mccarty", "mcdowell",
    "mcgee", "mckay", "mckee", "mckenzie", "mclean", "mcmahon", "mcneil",
    "meadows", "melton", "meyers", "middleton", "milton", "miranda", "monroe",
    "abbott", "acosta", "adkins", "aguirre", "albert", "albright", "alford",
    "allison", "amos", "andrade", "avila", "baird", "baldwin", "ball", "barber",
    "barrett", "barton", "bass", "bates", "beasley", "beck", "becker", "bender",
    "berger", "bernard", "blackburn", "blair", "blake", "blanchard", "boone",
    "bowen", "bowman", "boyer", "brady", "branch", "bray", "brennan", "brewer",
    "bridges", "briggs", "bright", "brock", "buck", "buckley", "burnett",
    "burris", "bush", "byrd", "cain", "camacho", "cannon", "cantrell", "carey",
    "carlson", "carr", "case", "chase", "christian", "clay", "clayton", "clemons",
    "clifton", "coffey", "collier", "conner", "conrad", "correa", "cortez",
    "costa", "cowan", "crane", "craven", "crow", "crowe", "cummings", "curtis",
    "dalton", "daugherty", "dean", "dejesus", "delacruz", "dempsey", "dickerson",
    "dickson", "dillard", "dillon", "dorsey", "dotson", "draper", "drew", "duke",
    "duran", "dyer", "elias", "emerson", "espinoza", "estes", "ewing", "farr",
    "fields", "finch", "fitch", "fitzgerald", "fletcher", "flowers", "flynn",
    "franco", "french", "frost", "fuller", "gaines", "galloway", "gates", "gay",
    "gibbs", "giles", "gilmore", "golden", "good", "grace", "grady", "griffith",
    "hammond", "hanson", "harding", "harrell", "hendricks", "herman", "hodge",
    "hodges", "hoffman", "holland", "holloway", "holt", "hood", "hooper", "house",
    "howell", "huff", "hurley", "jarvis", "joseph", "kendall", "kent", "kirkland",
    "knox", "krueger", "lamb", "landry", "lang", "larsen", "lim", "lloyd", "lowe",
    "madden", "mann", "manning", "marino", "marks", "massey", "mathis",
    "mccauley", "mccormick", "mcfarland", "mcguire", "mcintosh", "mckinney",
    "mcknight", "mcmillan", "miles", "montgomery", "montoya", "moody", "moon",
    "moran", "morse", "morton", "moss", "moyer", "mullins", "nash", "neal",
    "newman", "newton", "noble", "nolan", "norton", "obrien", "oneal", "orr",
    "osborne", "page", "parish", "parrish", "parsons", "pate", "patton", "paul",
    "pearson", "pena", "phelps", "pitts", "pope", "potter", "powers", "pratt",
    "preston", "proctor", "quinn", "ramsey", "randall", "rangel", "rasmussen",
    "reese", "reid", "reilly", "rich", "richards", "roach", "roberson", "rodgers",
    "rollins", "rowe", "roy", "royal", "rubio", "salinas", "sampson", "sanderson",
    "savage", "schneider", "schroeder", "schultz", "schwartz", "sears", "sharp",
    "shelton", "shepherd", "sherman", "short", "sims", "singleton", "skinner",
    "slater", "small", "snow", "solis", "sosa", "stafford", "stanley", "stanton",
    "stark", "steele", "stein", "sterling", "stokes", "strickland", "strong",
    "stump", "summers", "sutton", "swanson", "sweeney", "tate", "terrell",
    "terry", "todd", "townsend", "travis", "trujillo", "tyler", "underwood",
    "valdez", "valencia", "valentine", "valenzuela", "vance", "vaughan", "vaughn",
    "velasquez", "velazquez", "vera", "vincent", "wade", "waits", "wall", "walsh",
    "walters", "warner", "watkins", "watts", "weber", "weiss", "welch", "wheeler",
    "whitaker", "whitehead", "whitley", "wilcox", "wiley", "wilkins", "winters",
    "wise", "wolf", "wolfe", "woodard", "woodward", "wyatt", "yates", "york",
    "zamora", "zuniga", "abernathy", "ackerman", "adair", "addison", "ainsworth",
    "akers", "alden", "allred", "alonso", "ames", "anthony", "applegate",
    "arbuckle", "archer", "ashby", "ashford", "atkins", "arroyo", "atkinson",
    "austin", "avery", "ayers", "bachman", "bagley", "bain", "baxter", "barrios",
    "beal", "beard", "beaumont", "beckett", "bedford", "belcher", "bentley",
    "bergman", "batista", "best", "bishop", "blackwell", "blevins", "bolton",
    "bond", "booth", "bradshaw", "benitez", "brandt", "bryan", "buchanan",
    "bullock", "burch", "burgess", "burgin", "burkett", "blanco", "burnham",
    "cabot", "calhoun", "callahan", "carver", "cassidy", "chambers", "chaney",
    "bravo", "childress", "church", "clarke", "cobb", "cochran", "colby", "combs",
    "cooke", "cabrera", "cope", "copeland", "corbett", "cotton", "courtney",
    "covington", "crabtree", "crosby", "calderon", "cullen", "dailey", "dale",
    "darby", "davidson", "day", "deal", "denton", "campos", "dewitt", "dodson",
    "donovan", "doyle", "driscoll", "dyson", "eastman", "eddy", "cardenas",
    "elkins", "ellison", "emery", "estep", "everett", "fairchild", "faulkner",
    "felton", "carrillo", "fenton", "fitzpatrick", "forbes", "forrest", "frye",
    "fulton", "gamble", "gardiner", "cervantes", "garrett", "gilliam", "goff",
    "goodrich", "gorman", "gould", "granger", "gunn", "contreras", "haley",
    "hanna", "hargrove", "harmon", "harlan", "haskell", "hastings", "hawthorne",
    "cordova", "haynes", "hayward", "hebert", "hedrick", "hensley", "hess",
    "hewitt", "hickman", "delarosa", "hobbs", "hogan", "holbrook", "holcomb",
    "holden", "hollis", "holman", "hoyt", "duarte", "hull", "hyde", "jamison",
    "jeter", "keating", "kellogg", "kelsey", "kendrick", "escobar", "kincaid",
    "kingsley", "kramer", "lacey", "lassiter", "latham", "layton", "ledbetter",
    "espinosa", "levine", "lockhart", "lowery", "lynch", "lynn", "mabry", "mack",
    "macon", "fuentes", "maddox", "magee", "mahoney", "maloney", "mangum",
    "marlow", "mcbride", "mccoy", "gallardo", "mccray", "mcgrath", "mcintyre",
    "mckinley", "mcpherson", "merritt", "michaels", "miner", "garrido", "mobley",
    "moffett", "mooney", "morrow", "mosley", "murdock", "nance", "nixon",
    "guevara", "oakley", "odom", "oliver", "osborn", "oswald", "overton", "owen",
    "pace", "ibarra", "paine", "parks", "parr", "peck", "pemberton", "pennington",
    "perkins", "pettit", "lara", "pickett", "pike", "pinkerton", "platt", "poole",
    "prescott", "prince", "pruitt", "leon", "purcell", "radcliffe", "ragland",
    "rand", "ransom", "rawlings", "reeves", "rhodes", "lozano", "richmond",
    "ridley", "rigby", "riggs", "roark", "robbins", "rockwell", "rodman", "luna",
    "rosenberg", "rush", "rutledge", "sanford", "satterfield", "sawyer", "saxton",
    "scanlon", "marquez", "schaefer", "seymour", "shannon", "sheldon", "shepard",
    "sheridan", "shields", "shirley", "mejia", "simms", "sinclair", "sloan",
    "sparks", "spears", "stallings", "stapleton", "starr", "molina", "stevenson",
    "stockton", "sumner", "swift", "tanner", "tatum", "thornton", "tillman",
    "tomlinson", "tripp", "tyson", "upton", "vann", "vogel", "waddell", "walden",
    "wallis", "walton", "ware", "wayne", "weston", "whitfield", "whitman",
    "wilder", "wilkerson", "willard", "winslow", "winston", "witt",
]

DOMAINS = [
    "gmail.com",
]


def random_case(text):
    return text.lower()


def random_date_suffix():

    # Choose a year between 1952 and 2025.
    year = random.randint(
        1952,
        2025,
    )

    # Return either a 2-digit
    # or 4-digit representation.
    if random.choice(
        [
            True,
            False,
        ]
    ):

        return str(year)[-2:]

    return str(year)


def sanitize(value):
    return re.sub(
        r"[^a-zA-Z0-9]",
        "",
        value,
    ).lower()


def create_local_part():

    # Exactly ONE first name
    first = sanitize(
        random.choice(FIRST_NAMES)
    )

    # Exactly ONE last name
    last = sanitize(
        random.choice(LAST_NAMES)
    )

    roll = random.random()

    # ==================================================
    # 70% — FIRST + LAST + 2 OR 4 DIGIT YEAR
    # ==================================================
    if roll < 0.70:

        separator = random.choice(
            [
                ".",
                "_",
                "",
            ]
        )

        date_suffix = random_date_suffix()

        local = (
            f"{first}"
            f"{separator}"
            f"{last}"
            f"{date_suffix}"
        )

    # ==================================================
    # 5% — FIRST + LAST + SINGLE DIGIT 1–9
    # ==================================================
    elif roll < 0.75:

        separator = random.choice(
            [
                ".",
                "_",
                "",
            ]
        )

        number = random.randint(
            1,
            9,
        )

        local = (
            f"{first}"
            f"{separator}"
            f"{last}"
            f"{number}"
        )

    # ==================================================
    # 5% — FULL NAME, NO DOT, NO UNDERSCORE, NO NUMBER
    # ==================================================
    elif roll < 0.80:

        local = (
            f"{first}"
            f"{last}"
        )

    # ==================================================
    # 20% — NORMAL NAME, NO NUMBER
    # ==================================================
    else:

        separator = random.choice(
            [
                ".",
                "_",
                "",
            ]
        )

        local = (
            f"{first}"
            f"{separator}"
            f"{last}"
        )

    return local.lower()


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

    
    

    

    