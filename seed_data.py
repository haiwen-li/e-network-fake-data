"""Seed the database with Epstein network entities and relationships from public court records.

Sources: SDNY indictments (2019, 2020, 2021), Maxwell deposition (2016),
         Giuffre complaint (2015), Palm Beach police report (2005-2006),
         and other publicly released documents.
"""
from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.models.entity import Entity
from src.models.relationship import Relationship
from src.tools.storage_tools import upsert_entity, insert_relationship, relationship_exists, upsert_document
from src.models.document import Document

# Register source documents (as already-processed)
DOCS = [
    Document(id="sdny-indictment-2019", title="SDNY Indictment of Epstein (2019)", url="", source="justice.gov", date="2019-07-08", status="processed"),
    Document(id="maxwell-sdny-2020", title="SDNY Indictment of Maxwell (2020)", url="", source="justice.gov", date="2020-06-29", status="processed"),
    Document(id="maxwell-sdny-2021", title="SDNY Superseding Indictment of Maxwell (2021)", url="", source="justice.gov", date="2021-03-29", status="processed"),
    Document(id="maxwell-depo-2016", title="Maxwell Deposition 2016", url="", source="courtlistener", date="2016-04-22", status="processed"),
    Document(id="giuffre-complaint-2015", title="Giuffre Complaint 2015", url="", source="courtlistener", date="2015-12-30", status="processed"),
    Document(id="palm-beach-2005", title="Palm Beach Police Report 2005", url="", source="archive.org", date="2006-05-01", status="processed"),
    Document(id="acosta-npa-2008", title="Non-Prosecution Agreement 2008", url="", source="courtlistener", date="2008-09-24", status="processed"),
    Document(id="flight-logs", title="Epstein Flight Logs", url="", source="archive.org", date="2015-01-01", status="processed"),
    Document(id="maxwell-sentencing-2022", title="Maxwell Sentencing Memo 2022", url="", source="courtlistener", date="2022-06-28", status="processed"),
    Document(id="doe-unsealed-2024", title="Unsealed Documents 2024", url="", source="courtlistener", date="2024-01-03", status="processed"),
]

# ── Entities ──────────────────────────────────────────────────────────────────

ENTITIES = [
    # Central figures
    Entity(id="jeffrey-epstein", name="Jeffrey Epstein", entity_type="person", role="businessman",
           description="American financier convicted of sex trafficking; central node of the network. "
                       "Owner of multiple properties used in the trafficking operation.",
           aliases=["Jeff Epstein"]),

    Entity(id="ghislaine-maxwell", name="Ghislaine Maxwell", entity_type="person", role="socialite",
           description="British socialite convicted of sex trafficking in 2021. "
                       "Epstein's primary associate and co-conspirator in recruiting victims.",
           aliases=["Maxwell"]),

    # Alleged co-conspirators / associates named in court documents
    Entity(id="jean-luc-brunel", name="Jean-Luc Brunel", entity_type="person", role="businessman",
           description="French modeling agent named in Maxwell indictment as co-conspirator. "
                       "Died in French custody while awaiting trial in 2022.",
           aliases=["Brunel"]),

    Entity(id="sarah-ransome", name="Sarah Ransome", entity_type="person", role="other",
           description="Epstein victim and whistleblower; named in multiple court filings.",
           aliases=[]),

    Entity(id="virginia-giuffre", name="Virginia Giuffre", entity_type="person", role="other",
           description="Primary Epstein victim and plaintiff in Giuffre v. Maxwell. "
                       "Her deposition and complaint named dozens of associates.",
           aliases=["Virginia Roberts", "Giuffre"]),

    Entity(id="alan-dershowitz", name="Alan Dershowitz", entity_type="person", role="legal",
           description="Harvard law professor and Epstein's defense attorney. "
                       "Named in Giuffre complaint; filed multiple counter-suits.",
           aliases=["Dershowitz"]),

    Entity(id="prince-andrew", name="Prince Andrew", entity_type="person", role="royal",
           description="Duke of York; named in Giuffre deposition as a participant. "
                       "Settled civil lawsuit with Virginia Giuffre in 2022.",
           aliases=["Duke of York", "Andrew Windsor"]),

    Entity(id="bill-clinton", name="Bill Clinton", entity_type="person", role="politician",
           description="42nd US President; appeared on flight logs multiple times. "
                       "Named in various court documents in connection with Epstein.",
           aliases=["Clinton"]),

    Entity(id="donald-trump", name="Donald Trump", entity_type="person", role="politician",
           description="45th US President; appeared in early flight log entries. "
                       "Named in deposition as a social acquaintance of Epstein.",
           aliases=["Trump"]),

    Entity(id="les-wexner", name="Les Wexner", entity_type="person", role="businessman",
           description="Billionaire founder of L Brands (Victoria's Secret). "
                       "Gave Epstein power of attorney; primary financial patron. "
                       "Source of Epstein's New York mansion and much of his wealth.",
           aliases=["Leslie Wexner", "Wexner"]),

    Entity(id="alex-acosta", name="Alex Acosta", entity_type="person", role="legal",
           description="Former US Attorney (Southern District of Florida) who negotiated the "
                       "controversial 2008 non-prosecution agreement with Epstein. "
                       "Later served as Trump's Labor Secretary, resigned 2019.",
           aliases=["Acosta"]),

    Entity(id="peter-berliner", name="Peter Berliner", entity_type="person", role="legal",
           description="Epstein's Florida defense attorney during 2008 NPA negotiations.",
           aliases=[]),

    Entity(id="jay-lefkowitz", name="Jay Lefkowitz", entity_type="person", role="legal",
           description="Epstein attorney during 2008 negotiations; former Bush administration official.",
           aliases=["Lefkowitz"]),

    Entity(id="darren-indyke", name="Darren Indyke", entity_type="person", role="legal",
           description="Epstein's longtime lawyer and executor of his estate.",
           aliases=["Indyke"]),

    Entity(id="richard-kahn", name="Richard Kahn", entity_type="person", role="legal",
           description="Epstein's accountant; co-executor of the estate with Indyke.",
           aliases=["Kahn"]),

    Entity(id="eva-andersson-dubin", name="Eva Andersson-Dubin", entity_type="person", role="socialite",
           description="Swedish physician and socialite; former girlfriend of Epstein. "
                       "Named in Maxwell deposition.",
           aliases=["Eva Dubin"]),

    Entity(id="glenn-dubin", name="Glenn Dubin", entity_type="person", role="businessman",
           description="Billionaire hedge fund manager; husband of Eva Andersson-Dubin. "
                       "Named in Maxwell deposition as Epstein associate.",
           aliases=["Dubin"]),

    Entity(id="naomi-campbell", name="Naomi Campbell", entity_type="person", role="other",
           description="British supermodel; appeared in Maxwell deposition as someone Maxwell knew.",
           aliases=["Campbell"]),

    Entity(id="heidi-klum", name="Heidi Klum", entity_type="person", role="other",
           description="German-American model; briefly mentioned in Maxwell deposition.",
           aliases=["Klum"]),

    Entity(id="senator-george-mitchell", name="George Mitchell", entity_type="person", role="politician",
           description="Former US Senator and Middle East envoy; named in Giuffre deposition.",
           aliases=["Mitchell"]),

    Entity(id="richard-branson", name="Richard Branson", entity_type="person", role="businessman",
           description="British billionaire; named in unsealed 2024 documents.",
           aliases=["Branson"]),

    Entity(id="stephen-hawking", name="Stephen Hawking", entity_type="person", role="other",
           description="Famed physicist; named in 2024 unsealed documents as having attended "
                       "a conference at Epstein's island.",
           aliases=["Hawking"]),

    Entity(id="peter-mandelson", name="Peter Mandelson", entity_type="person", role="politician",
           description="British politician; named in Maxwell deposition as an associate.",
           aliases=["Mandelson"]),

    Entity(id="ehud-barak", name="Ehud Barak", entity_type="person", role="politician",
           description="Former Israeli Prime Minister; named in court documents as an Epstein associate. "
                       "Acknowledged visiting Epstein properties.",
           aliases=["Barak"]),

    Entity(id="lawrence-krauss", name="Lawrence Krauss", entity_type="person", role="other",
           description="Theoretical physicist; named as Epstein associate in 2024 documents.",
           aliases=["Krauss"]),

    Entity(id="leon-black", name="Leon Black", entity_type="person", role="businessman",
           description="Apollo Global Management founder; paid Epstein $158M in fees. "
                       "Named in multiple court documents.",
           aliases=["Black"]),

    Entity(id="mort-zuckerman", name="Mort Zuckerman", entity_type="person", role="businessman",
           description="Real estate mogul and media owner; named in Maxwell deposition.",
           aliases=["Zuckerman"]),

    Entity(id="michael-bloomberg", name="Michael Bloomberg", entity_type="person", role="politician",
           description="Former NYC Mayor and businessman; named briefly in Maxwell deposition.",
           aliases=["Bloomberg"]),

    Entity(id="david-copperfield", name="David Copperfield", entity_type="person", role="other",
           description="Illusionist; named in 2024 unsealed documents.",
           aliases=["Copperfield"]),

    Entity(id="mark-epstein", name="Mark Epstein", entity_type="person", role="businessman",
           description="Jeffrey Epstein's brother; named in court documents.",
           aliases=["M. Epstein"]),

    Entity(id="jes-staley", name="Jes Staley", entity_type="person", role="businessman",
           description="Former Barclays CEO; named in 2024 unsealed documents as an Epstein associate "
                       "with hundreds of email exchanges.",
           aliases=["Staley"]),

    Entity(id="david-rodgers", name="David Rodgers", entity_type="person", role="other",
           description="Named in 2024 unsealed documents.",
           aliases=[]),

    Entity(id="adriana-ross", name="Adriana Ross", entity_type="person", role="other",
           description="Epstein associate named in Maxwell indictment as assisting in the operation.",
           aliases=["Marcinkova"]),

    Entity(id="nadia-marcinkova", name="Nadia Marcinkova", entity_type="person", role="other",
           description="Epstein associate named as a participant in the trafficking operation; "
                       "later became a pilot.",
           aliases=["Marcinkova", "Global Girl"]),

    Entity(id="sarah-kellen", name="Sarah Kellen", entity_type="person", role="other",
           description="Epstein's personal assistant; named as a co-conspirator in Maxwell indictment.",
           aliases=["Sarah Kensington"]),

    Entity(id="lesley-groff", name="Lesley Groff", entity_type="person", role="other",
           description="Epstein's executive assistant; named in Maxwell indictment.",
           aliases=["Groff"]),

    # Organizations
    Entity(id="sdny", name="SDNY (US Attorney's Office)", entity_type="organization", role="legal",
           description="Southern District of New York — prosecuted both Epstein (2019) and Maxwell (2020-2021).",
           aliases=["Southern District of New York"]),

    Entity(id="palm-beach-pd", name="Palm Beach Police Department", entity_type="organization", role="legal",
           description="First law enforcement agency to investigate Epstein in 2005-2006.",
           aliases=["PBPD"]),

    Entity(id="fbi", name="FBI", entity_type="organization", role="legal",
           description="Federal Bureau of Investigation; co-investigators in Epstein case.",
           aliases=["Federal Bureau of Investigation"]),

    Entity(id="doj", name="US Department of Justice", entity_type="organization", role="legal",
           description="Oversaw the NPA in 2008 and the 2019 prosecution.",
           aliases=["DOJ"]),

    Entity(id="l-brands", name="L Brands / Victoria's Secret", entity_type="organization", role="businessman",
           description="Les Wexner's retail empire; Epstein used this connection to recruit models.",
           aliases=["L Brands", "Victoria's Secret"]),

    Entity(id="jeffrey-epstein-foundation", name="Jeffrey Epstein VI Foundation", entity_type="organization", role="ngo",
           description="Epstein's charitable foundation used to cultivate academic and scientific contacts.",
           aliases=["Epstein Foundation"]),

    Entity(id="mit-media-lab", name="MIT Media Lab", entity_type="organization", role="ngo",
           description="Received $850K in donations from Epstein after his 2008 conviction. "
                       "Director Joi Ito resigned when donations were revealed.",
           aliases=["MIT"]),

    Entity(id="harvard-university", name="Harvard University", entity_type="organization", role="ngo",
           description="Received $6.5M from Epstein. Multiple faculty had connections to Epstein.",
           aliases=["Harvard"]),

    Entity(id="jpmorgan-chase", name="JPMorgan Chase", entity_type="organization", role="businessman",
           description="Epstein's primary bank for years; sued by USVI for facilitating trafficking. "
                       "Settled for $290M in 2023.",
           aliases=["JPMorgan"]),

    Entity(id="deutsche-bank", name="Deutsche Bank", entity_type="organization", role="businessman",
           description="Banked Epstein after JPMorgan dropped him; settled with USVI for $75M in 2023.",
           aliases=[]),

    Entity(id="mc2-model-management", name="MC2 Model Management", entity_type="organization", role="businessman",
           description="Jean-Luc Brunel's modeling agency; used as a pipeline for recruiting victims.",
           aliases=["MC2"]),

    # Locations
    Entity(id="little-st-james", name="Little St. James Island", entity_type="location", role="other",
           description="Epstein's private island in the US Virgin Islands; primary location of abuse. "
                       "Known as 'Pedophile Island' locally.",
           aliases=["Pedophile Island", "Little Saint James", "USVI Island"]),

    Entity(id="great-st-james", name="Great St. James Island", entity_type="location", role="other",
           description="Adjacent island purchased by Epstein in 2016.",
           aliases=["Great Saint James"]),

    Entity(id="71-zorro-ranch", name="Zorro Ranch (New Mexico)", entity_type="location", role="other",
           description="Epstein's 10,000-acre ranch near Stanley, New Mexico; "
                       "site of alleged trafficking.",
           aliases=["Zorro Ranch", "New Mexico ranch"]),

    Entity(id="9-east-71st", name="9 East 71st Street, New York", entity_type="location", role="other",
           description="Epstein's Manhattan townhouse; one of the largest private residences in NYC. "
                       "Originally owned by Les Wexner.",
           aliases=["East 71st Street mansion", "NY mansion"]),

    Entity(id="palm-beach-mansion", name="Palm Beach Mansion (El Brillo Way)", entity_type="location", role="other",
           description="Epstein's Palm Beach estate; site of original 2005-2006 police investigation.",
           aliases=["358 El Brillo Way", "Palm Beach estate"]),

    Entity(id="paris-apartment", name="Paris Apartment (Avenue Foch)", entity_type="location", role="other",
           description="Epstein's Paris apartment on Avenue Foch, near the Champs-Élysées.",
           aliases=["Paris flat"]),

    # Vessels
    Entity(id="lolita-express", name="Lolita Express", entity_type="vessel", role="other",
           description="Epstein's Boeing 727 private jet; flight logs showed dozens of notable passengers.",
           aliases=["Epstein's jet", "Boeing 727"]),

    Entity(id="epstein-helicopter", name="Epstein's Helicopter", entity_type="vessel", role="other",
           description="Helicopter used to transport guests to Little St. James Island.",
           aliases=[]),
]

# ── Relationships ─────────────────────────────────────────────────────────────

RELATIONSHIPS = [
    # Epstein → Maxwell
    ("jeffrey-epstein", "ghislaine-maxwell", "associated", "strong", "sdny-indictment-2019",
     "Maxwell served as Epstein's primary co-conspirator and associate for decades"),

    # Epstein → Victims
    ("jeffrey-epstein", "virginia-giuffre", "accused", "strong", "giuffre-complaint-2015",
     "Giuffre alleged Epstein trafficked her beginning when she was 17"),

    ("jeffrey-epstein", "sarah-ransome", "accused", "strong", "doe-unsealed-2024",
     "Ransome alleged Epstein sexually abused her at multiple properties"),

    # Maxwell → Victims (recruiting)
    ("ghislaine-maxwell", "virginia-giuffre", "accused", "strong", "maxwell-sdny-2020",
     "Maxwell recruited Giuffre as a minor; convicted of this offense in 2021"),

    ("ghislaine-maxwell", "sarah-ransome", "accused", "strong", "maxwell-sdny-2021",
     "Ransome named Maxwell as involved in her trafficking"),

    # Epstein → Co-conspirators
    ("jeffrey-epstein", "jean-luc-brunel", "associated", "strong", "maxwell-sdny-2020",
     "Brunel named as co-conspirator in Maxwell indictment; ran MC2 as victim pipeline"),

    ("jeffrey-epstein", "sarah-kellen", "employed", "strong", "maxwell-sdny-2020",
     "Kellen served as Epstein's personal assistant and named co-conspirator"),

    ("jeffrey-epstein", "lesley-groff", "employed", "strong", "maxwell-sdny-2021",
     "Groff served as executive assistant and was named in the superseding indictment"),

    ("jeffrey-epstein", "nadia-marcinkova", "associated", "strong", "giuffre-complaint-2015",
     "Marcinkova named as participant in trafficking operation"),

    ("jeffrey-epstein", "adriana-ross", "associated", "strong", "maxwell-sdny-2020",
     "Ross named as assisting Maxwell and Epstein in the operation"),

    # Epstein → Financial associates
    ("jeffrey-epstein", "les-wexner", "associated", "strong", "giuffre-complaint-2015",
     "Wexner gave Epstein power of attorney and was his primary financial patron"),

    ("jeffrey-epstein", "leon-black", "associated", "strong", "doe-unsealed-2024",
     "Black paid Epstein $158M in fees; named in unsealed 2024 documents"),

    ("jeffrey-epstein", "jes-staley", "associated", "strong", "doe-unsealed-2024",
     "Hundreds of emails between Staley and Epstein; Staley visited Epstein properties"),

    ("jeffrey-epstein", "darren-indyke", "employed", "strong", "sdny-indictment-2019",
     "Indyke served as Epstein's longtime lawyer and estate executor"),

    ("jeffrey-epstein", "richard-kahn", "employed", "strong", "sdny-indictment-2019",
     "Kahn served as Epstein's accountant and co-executor"),

    ("jeffrey-epstein", "mark-epstein", "associated", "strong", "giuffre-complaint-2015",
     "Mark Epstein named as brother and associate of Jeffrey"),

    # Epstein → Politicians / public figures (flight logs / depositions)
    ("jeffrey-epstein", "bill-clinton", "flew_with", "strong", "flight-logs",
     "Clinton appeared on Epstein's flight logs at least 26 times"),

    ("jeffrey-epstein", "donald-trump", "flew_with", "weak", "flight-logs",
     "Trump appeared on early flight logs; later distanced himself from Epstein"),

    ("jeffrey-epstein", "prince-andrew", "met_with", "strong", "maxwell-depo-2016",
     "Maxwell confirmed Epstein and Prince Andrew's friendship in 2016 deposition"),

    ("jeffrey-epstein", "alan-dershowitz", "employed", "strong", "acosta-npa-2008",
     "Dershowitz was lead attorney who negotiated the 2008 NPA with Acosta"),

    ("jeffrey-epstein", "ehud-barak", "met_with", "strong", "doe-unsealed-2024",
     "Barak acknowledged visiting Epstein properties multiple times"),

    ("jeffrey-epstein", "george-mitchell", "met_with", "weak", "giuffre-complaint-2015",
     "Giuffre named Mitchell in her complaint; Mitchell denied all allegations"),

    ("jeffrey-epstein", "richard-branson", "met_with", "weak", "doe-unsealed-2024",
     "Named in 2024 unsealed documents as an acquaintance"),

    # Epstein → Academic/Science connections
    ("jeffrey-epstein", "stephen-hawking", "met_with", "weak", "doe-unsealed-2024",
     "Hawking attended a science conference at Epstein's island"),

    ("jeffrey-epstein", "lawrence-krauss", "associated", "weak", "doe-unsealed-2024",
     "Krauss was a regular at Epstein's New York home; named as associate"),

    ("jeffrey-epstein", "mit-media-lab", "funded", "strong", "doe-unsealed-2024",
     "Epstein donated $850K to MIT Media Lab after his 2008 conviction"),

    ("jeffrey-epstein", "harvard-university", "funded", "strong", "doe-unsealed-2024",
     "Epstein donated $6.5M to Harvard; maintained close ties with faculty"),

    ("jeffrey-epstein", "jeffrey-epstein-foundation", "funded", "strong", "sdny-indictment-2019",
     "Epstein ran foundation to cultivate scientific and academic relationships"),

    # Epstein → Banks
    ("jeffrey-epstein", "jpmorgan-chase", "associated", "strong", "doe-unsealed-2024",
     "JPMorgan was Epstein's primary bank; later sued for facilitating trafficking"),

    ("jeffrey-epstein", "deutsche-bank", "associated", "strong", "doe-unsealed-2024",
     "Deutsche Bank took Epstein after JPMorgan; settled USVI lawsuit for $75M"),

    # Epstein → Properties
    ("jeffrey-epstein", "little-st-james", "owned_property", "strong", "sdny-indictment-2019",
     "Epstein owned Little St. James Island; primary site of abuse per indictment"),

    ("jeffrey-epstein", "great-st-james", "owned_property", "strong", "sdny-indictment-2019",
     "Epstein purchased Great St. James in 2016"),

    ("jeffrey-epstein", "71-zorro-ranch", "owned_property", "strong", "sdny-indictment-2019",
     "Epstein owned Zorro Ranch in New Mexico; named in indictment as abuse site"),

    ("jeffrey-epstein", "9-east-71st", "owned_property", "strong", "sdny-indictment-2019",
     "NYC townhouse originally owned by Wexner; given to Epstein"),

    ("jeffrey-epstein", "palm-beach-mansion", "owned_property", "strong", "palm-beach-2005",
     "Palm Beach estate; site of original 2005 police investigation"),

    ("jeffrey-epstein", "paris-apartment", "owned_property", "strong", "maxwell-depo-2016",
     "Paris apartment mentioned in Maxwell deposition"),

    ("jeffrey-epstein", "lolita-express", "owned_property", "strong", "flight-logs",
     "Epstein owned the Boeing 727 jet documented in flight logs"),

    # Maxwell → associates
    ("ghislaine-maxwell", "jean-luc-brunel", "associated", "strong", "maxwell-sdny-2020",
     "Maxwell and Brunel co-ran the recruitment network per indictment"),

    ("ghislaine-maxwell", "prince-andrew", "met_with", "strong", "maxwell-depo-2016",
     "Maxwell confirmed long friendship with Prince Andrew in deposition"),

    ("ghislaine-maxwell", "alan-dershowitz", "associated", "weak", "giuffre-complaint-2015",
     "Both named in Giuffre complaint as associates of Epstein"),

    ("ghislaine-maxwell", "naomi-campbell", "associated", "weak", "maxwell-depo-2016",
     "Maxwell mentioned knowing Campbell in deposition"),

    ("ghislaine-maxwell", "eva-andersson-dubin", "met_with", "weak", "maxwell-depo-2016",
     "Both mentioned in Maxwell deposition as social acquaintances"),

    ("ghislaine-maxwell", "peter-mandelson", "met_with", "weak", "maxwell-depo-2016",
     "Mandelson named in Maxwell deposition as an associate"),

    ("ghislaine-maxwell", "sarah-kellen", "associated", "strong", "maxwell-sdny-2020",
     "Kellen worked directly with Maxwell in the trafficking operation"),

    # Legal / prosecution relationships
    ("alex-acosta", "jeffrey-epstein", "associated", "strong", "acosta-npa-2008",
     "Acosta negotiated the secret non-prosecution agreement in 2008"),

    ("alan-dershowitz", "alex-acosta", "met_with", "strong", "acosta-npa-2008",
     "Dershowitz negotiated directly with Acosta on Epstein's behalf"),

    ("sdny", "jeffrey-epstein", "accused", "strong", "sdny-indictment-2019",
     "SDNY indicted Epstein on sex trafficking charges in July 2019"),

    ("sdny", "ghislaine-maxwell", "accused", "strong", "maxwell-sdny-2020",
     "SDNY indicted Maxwell in June 2020 on six counts of sex trafficking"),

    ("palm-beach-pd", "jeffrey-epstein", "accused", "strong", "palm-beach-2005",
     "PBPD investigated Epstein from 2005-2006; referred case to FBI"),

    ("palm-beach-pd", "doj", "associated", "strong", "acosta-npa-2008",
     "PBPD referred the case to the DOJ which negotiated the NPA"),

    ("fbi", "jeffrey-epstein", "accused", "strong", "sdny-indictment-2019",
     "FBI co-investigated with SDNY; arrested Epstein at Teterboro Airport in 2019"),

    # Wexner / financial ties
    ("les-wexner", "l-brands", "associated", "strong", "giuffre-complaint-2015",
     "Wexner founded L Brands; Epstein used the connection to recruit models"),

    ("les-wexner", "9-east-71st", "owned_property", "strong", "giuffre-complaint-2015",
     "Wexner originally owned the NYC mansion and transferred it to Epstein"),

    ("jean-luc-brunel", "mc2-model-management", "associated", "strong", "maxwell-sdny-2020",
     "Brunel ran MC2; SDNY indictment described it as a vehicle for victim recruitment"),

    # Social connections
    ("ghislaine-maxwell", "mort-zuckerman", "met_with", "weak", "maxwell-depo-2016",
     "Zuckerman named in Maxwell deposition as a social acquaintance"),

    ("jeffrey-epstein", "mort-zuckerman", "met_with", "weak", "maxwell-depo-2016",
     "Zuckerman named in Maxwell deposition"),

    ("jeffrey-epstein", "michael-bloomberg", "met_with", "weak", "maxwell-depo-2016",
     "Bloomberg briefly mentioned in Maxwell deposition"),

    ("jeffrey-epstein", "david-copperfield", "met_with", "weak", "doe-unsealed-2024",
     "Copperfield named in 2024 unsealed documents"),

    ("jeffrey-epstein", "heidi-klum", "met_with", "weak", "maxwell-depo-2016",
     "Klum briefly mentioned in Maxwell deposition"),

    ("jeffrey-epstein", "eva-andersson-dubin", "associated", "weak", "maxwell-depo-2016",
     "Eva Andersson-Dubin was Epstein's former girlfriend; named in deposition"),

    ("jeffrey-epstein", "glenn-dubin", "associated", "weak", "maxwell-depo-2016",
     "Glenn Dubin named in Maxwell deposition as an Epstein associate"),

    ("eva-andersson-dubin", "glenn-dubin", "associated", "strong", "maxwell-depo-2016",
     "Married couple; both connected to Epstein social circle"),

    ("jeffrey-epstein", "david-rodgers", "met_with", "weak", "doe-unsealed-2024",
     "Named in 2024 unsealed documents"),

    # Properties visited
    ("virginia-giuffre", "little-st-james", "met_with", "strong", "giuffre-complaint-2015",
     "Giuffre described being trafficked to Little St. James multiple times"),

    ("bill-clinton", "little-st-james", "met_with", "weak", "flight-logs",
     "Flight logs showed Clinton visiting the island"),

    ("prince-andrew", "little-st-james", "met_with", "strong", "giuffre-complaint-2015",
     "Giuffre alleged she was trafficked to Prince Andrew on the island"),

    ("virginia-giuffre", "9-east-71st", "met_with", "strong", "giuffre-complaint-2015",
     "Giuffre described abuse at Epstein's NYC townhouse"),

    ("virginia-giuffre", "palm-beach-mansion", "met_with", "strong", "giuffre-complaint-2015",
     "Giuffre's trafficking began at the Palm Beach estate"),

    # MIT / Harvard
    ("jeffrey-epstein-foundation", "mit-media-lab", "funded", "strong", "doe-unsealed-2024",
     "Foundation funneled $850K to MIT Media Lab"),

    ("jeffrey-epstein-foundation", "harvard-university", "funded", "strong", "doe-unsealed-2024",
     "Foundation donated millions to Harvard programs"),

    # Flight log connections
    ("bill-clinton", "lolita-express", "flew_with", "strong", "flight-logs",
     "Clinton logged on Epstein's jet 26 times per flight logs"),

    ("ghislaine-maxwell", "lolita-express", "flew_with", "strong", "flight-logs",
     "Maxwell frequently flew on Epstein's jet"),

    ("virginia-giuffre", "lolita-express", "flew_with", "strong", "flight-logs",
     "Giuffre named as a passenger on Epstein's jet"),

    ("prince-andrew", "lolita-express", "flew_with", "strong", "flight-logs",
     "Prince Andrew appeared in flight logs"),

    ("alan-dershowitz", "lolita-express", "flew_with", "strong", "flight-logs",
     "Dershowitz appeared in flight logs; disputed some entries"),

    # Additional
    ("ghislaine-maxwell", "nadia-marcinkova", "associated", "strong", "maxwell-sdny-2021",
     "Marcinkova named in Maxwell superseding indictment"),

    ("ghislaine-maxwell", "adriana-ross", "associated", "strong", "maxwell-sdny-2020",
     "Ross named as assisting Maxwell per indictment"),

    ("ghislaine-maxwell", "lesley-groff", "associated", "strong", "maxwell-sdny-2021",
     "Groff named in Maxwell's superseding indictment"),

    ("jes-staley", "jpmorgan-chase", "associated", "strong", "doe-unsealed-2024",
     "Staley worked at JPMorgan while maintaining email contact with Epstein"),
]


def main():
    print("Seeding documents...")
    for doc in DOCS:
        upsert_document(doc)
    print(f"  ✓ {len(DOCS)} documents registered")

    print("Seeding entities...")
    for entity in ENTITIES:
        upsert_entity(entity)
    print(f"  ✓ {len(ENTITIES)} entities inserted/updated")

    print("Seeding relationships...")
    count = 0
    for (from_id, to_id, rel_type, tie_strength, doc_id, context) in RELATIONSHIPS:
        if not relationship_exists(from_id, to_id, rel_type, doc_id):
            rel = Relationship(
                from_id=from_id,
                to_id=to_id,
                rel_type=rel_type,
                tie_strength=tie_strength,
                doc_id=doc_id,
                context=context,
            )
            insert_relationship(rel)
            count += 1
    print(f"  ✓ {count} relationships inserted")

    print("\nDone! Now run:")
    print("  python main.py build")
    print("  python main.py visualize")


if __name__ == "__main__":
    main()
