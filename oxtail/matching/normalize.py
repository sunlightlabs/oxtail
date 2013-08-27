from name_cleaver import IndividualNameCleaver, OrganizationNameCleaver, PoliticianNameCleaver
from name_cleaver.names import RunningMatesNames
import operator

def normalize_person(alias, cleaver):
    parts = cleaver(alias).parse(safe=True)
    
    if isinstance(parts, (str, unicode)):
        return [alias]
    
    if isinstance(parts, RunningMatesNames):
        return normalize_person(str(parts.mate1), PoliticianNameCleaver) + normalize_person(str(parts.mate2), PoliticianNameCleaver)
        
    permutations = [
        "%s %s" % (parts.first, parts.last),
        # caused too many false positives
#        "%s %s" % (parts.last, parts.first),
    ]
    if parts.middle:
        permutations.append("%s %s %s" % (parts.first, parts.middle, parts.last))
    
    return permutations

def normalize_organization(alias):
    parts = OrganizationNameCleaver(alias).parse(safe=True)

    if isinstance(parts, (str, unicode)):
        return [parts]

    standardized = parts.__str__()
    expanded = parts.expand()

    if standardized == expanded:
        return [standardized]
    else:
        return [standardized, expanded]



NORMALIZERS_BY_TYPE = {
   'individual': lambda x: normalize_person(x, IndividualNameCleaver),
   'organization': normalize_organization,
   'politician': lambda x: normalize_person(x, PoliticianNameCleaver),
   'industry': None,
}

def normalize(alias, type):
    _normalize = NORMALIZERS_BY_TYPE.get(type, None)
    if _normalize:
        return _normalize(alias)
    else:
        return []

def normalize_list(l, type):
    return reduce(operator.add, [normalize(item, type) for item in l])
