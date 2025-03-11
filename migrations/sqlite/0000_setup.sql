-- Combined Migration File for Traveller Campaign Database

CREATE TABLE sectors (
    sector_id INTEGER PRIMARY KEY,
    name TEXT,
    x_coordinate INTEGER,
    y_coordinate INTEGER,
    description TEXT,
    image_path TEXT
);

CREATE TABLE planets (
    planet_id INTEGER PRIMARY KEY,
    name TEXT,
    sector_id INTEGER,
    x_coordinate INTEGER,
    y_coordinate INTEGER,
    UPP TEXT,
    description TEXT,
    image_path TEXT,
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
);

CREATE TABLE people (
    person_id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER,
    gender TEXT,
    planet_id INTEGER,
    occupation_id INTEGER,
    UPP TEXT,
    biography TEXT,
    image_path TEXT,
    FOREIGN KEY (planet_id) REFERENCES planets(planet_id),
    FOREIGN KEY (occupation_id) REFERENCES occupations(occupation_id)
);

CREATE TABLE lifeforms (
    lifeform_id INTEGER PRIMARY KEY,
    name TEXT,
    planet_id INTEGER,
    classification TEXT,
    habitat_id INTEGER,
    diet_id INTEGER,
    behavior TEXT,
    description TEXT,
    image_path TEXT,
    FOREIGN KEY (planet_id) REFERENCES planets(planet_id),
    FOREIGN KEY (habitat_id) REFERENCES habitats(habitat_id),
    FOREIGN KEY (diet_id) REFERENCES diet_types(diet_id)
);

CREATE TABLE ships (
    ship_id INTEGER PRIMARY KEY,
    name TEXT,
    class_id INTEGER,
    owner_id INTEGER,
    sector_id INTEGER,
    description TEXT,
    image_path TEXT,
    FOREIGN KEY (class_id) REFERENCES ship_classes(class_id),
    FOREIGN KEY (owner_id) REFERENCES people(person_id),
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
);

CREATE TABLE ship_classes (
    class_id INTEGER PRIMARY KEY,
    class_name TEXT,
    description TEXT
);

CREATE TABLE vehicles (
    vehicle_id INTEGER PRIMARY KEY,
    name TEXT,
    type_id INTEGER,
    owner_id INTEGER,
    planet_id INTEGER,
    description TEXT,
    image_path TEXT,
    FOREIGN KEY (type_id) REFERENCES vehicle_types(type_id),
    FOREIGN KEY (owner_id) REFERENCES people(person_id),
    FOREIGN KEY (planet_id) REFERENCES planets(planet_id)
);

CREATE TABLE vehicle_types (
    type_id INTEGER PRIMARY KEY,
    type_name TEXT,
    description TEXT
);

CREATE TABLE technology (
    technology_id INTEGER PRIMARY KEY,
    name TEXT,
    type_id INTEGER,
    description TEXT,
    image_path TEXT,
    FOREIGN KEY (type_id) REFERENCES technology_types(type_id)
);

CREATE TABLE technology_types (
    type_id INTEGER PRIMARY KEY,
    type_name TEXT,
    description TEXT
);

CREATE TABLE organizations (
    organization_id INTEGER PRIMARY KEY,
    name TEXT,
    type_id INTEGER,
    description TEXT,
    headquarters_id INTEGER,
    sector_id INTEGER,
    FOREIGN KEY (type_id) REFERENCES organization_types(type_id),
    FOREIGN KEY (headquarters_id) REFERENCES planets(planet_id),
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id)
);

CREATE TABLE organization_types (
    type_id INTEGER PRIMARY KEY,
    type_name TEXT,
    description TEXT
);

CREATE TABLE events (
    event_id INTEGER PRIMARY KEY,
    name TEXT,
    date TEXT,
    description TEXT,
    sector_id INTEGER,
    planet_id INTEGER,
    FOREIGN KEY (sector_id) REFERENCES sectors(sector_id),
    FOREIGN KEY (planet_id) REFERENCES planets(planet_id)
);

CREATE TABLE adventure_hooks (
    hook_id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    planet_id INTEGER,
    person_id INTEGER,
    FOREIGN KEY (planet_id) REFERENCES planets(planet_id),
    FOREIGN KEY (person_id) REFERENCES people(person_id)
);

CREATE TABLE skills (
    skill_id INTEGER PRIMARY KEY,
    skill_name TEXT,
    description TEXT
);

CREATE TABLE person_skills (
    person_id INTEGER,
    skill_id INTEGER,
    level INTEGER,
    PRIMARY KEY (person_id, skill_id),
    FOREIGN KEY (person_id) REFERENCES people(person_id),
    FOREIGN KEY (skill_id) REFERENCES skills(skill_id)
);

CREATE TABLE lifeform_traits (
    trait_id INTEGER PRIMARY KEY,
    trait_name TEXT,
    description TEXT
);

CREATE TABLE lifeform_traits_rel (
    lifeform_id INTEGER,
    trait_id INTEGER,
    level INTEGER,
    PRIMARY KEY (lifeform_id, trait_id),
    FOREIGN KEY (lifeform_id) REFERENCES lifeforms(lifeform_id),
    FOREIGN KEY (trait_id) REFERENCES lifeform_traits(trait_id)
);

CREATE TABLE involved_parties (
    involvement_id INTEGER PRIMARY KEY,
    person_id INTEGER,
    organization_id INTEGER,
    event_id INTEGER,
    description TEXT,
    FOREIGN KEY (person_id) REFERENCES people(person_id),
    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id),
    FOREIGN KEY (event_id) REFERENCES events(event_id)
);

CREATE TABLE occupations (
    occupation_id INTEGER PRIMARY KEY,
    occupation_name TEXT,
    description TEXT
);

CREATE TABLE habitats (
    habitat_id INTEGER PRIMARY KEY,
    habitat_name TEXT,
    description TEXT
);

CREATE TABLE diet_types (
    diet_id INTEGER PRIMARY KEY,
    diet_name TEXT,
    description TEXT
);

-- Adventure Planner Table

CREATE TABLE IF NOT EXISTS adventure_elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phase INTEGER,
    table_name TEXT,
    table_id INTEGER,
    description TEXT
);
