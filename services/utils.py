from geoalchemy2.elements import WKTElement

def wkt_to_coordinates(wkt_element: WKTElement) -> list:
    """Convert WKTElement to a list of coordinates."""
    if wkt_element is None:
        return None
    # Extract the coordinates from the WKT string
    wkt = wkt_element.desc
    # Assuming it's a POINT, extract the coordinates
    if wkt.startswith("POINT"):
        coords = wkt.replace("POINT(", "").replace(")", "").split()
        return [float(coord) for coord in coords]
    return None


def risk_calculator(occurrences) -> str:

    OCCURRENCES_WEIGHTS = {
        "Theft": 4,
        "Strange Movement": 1,
        "Fight": 2,
        "Aggressive Person": 2,
        "Drugs": 3
    }
    risk = sum(OCCURRENCES_WEIGHTS.get(occ, 0) * count for occ, count in occurrences.items())

    if risk <= 10:
        return "Low"
    
    if risk <= 30:
        return "Average"
    
    return "High"


