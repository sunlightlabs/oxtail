from name_cleaver import PoliticianNameCleaver, OrganizationNameCleaver, \
        IndividualNameCleaver

_standardizers = {
    'politician': lambda n: PoliticianNameCleaver(n).parse(),
    'individual': lambda n: IndividualNameCleaver(n).parse(),
    'industry': lambda n: OrganizationNameCleaver(n).parse(),
    'organization': lambda n: OrganizationNameCleaver(n).parse(),
}

def standardize_name(name, type):
    return str(_standardizers[type](name))
