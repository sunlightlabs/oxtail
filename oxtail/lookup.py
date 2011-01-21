from SPARQLWrapper import SPARQLWrapper, JSON

def lookup_domain(domain):
    patterns = ['http://%s', 'http://www.%s', 'http://%s/', 'http://www.%s/', '%s']
    
    websites = map(lambda s: '?website = <%s>' % (s % domain), patterns)
    website = " || ".join(websites)
    
    urls = map(lambda s: '?website = "%s"@en' % (s % domain), patterns)
    url = " || ".join(urls)
    
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    
    # This version of the query also matches the URL field, but seems to do it
    # poorly, and slows the query way down; excluding for now
    #sparql.setQuery("""
    #    PREFIX foaf: <http://xmlns.com/foaf/0.1/>
    #    PREFIX dbpedia2: <http://dbpedia.org/property/>
    #    
    #    SELECT DISTINCT ?entity ?wikipedia_page ?name ?website
    #    WHERE {
    #        {
    #            ?entity foaf:page ?wikipedia_page .
    #            ?entity dbpedia2:name ?name .
    #            ?entity foaf:homepage ?website .
    #            FILTER( %s )
    #        } UNION
    #        {
    #            ?entity foaf:page ?wikipedia_page .
    #            ?entity dbpedia2:name ?name .
    #            ?entity dbpedia2:url ?website .
    #            FILTER( %s )
    #        }
    #    }
    #    LIMIT 10
    #""" % (website, url))
    
    sparql.setQuery("""
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX dbpedia2: <http://dbpedia.org/property/>
        
        SELECT DISTINCT ?entity ?wikipedia_page ?name ?website
        WHERE {
            ?entity foaf:page ?wikipedia_page .
            ?entity dbpedia2:name ?name .
            ?entity foaf:homepage ?website .
            FILTER( %s )
        }
        LIMIT 10
    """ % website)
    print sparql.queryString
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    
    out = []
    for result in results["results"]["bindings"]:
        out.append({'name': result['name']['value'], 'wikipedia_page': result['wikipedia_page']['value']})
    
    return out
