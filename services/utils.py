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


def email_confirmation(dst:str, token:str, username:str) -> dict:
    html_template = f"""
        <!DOCTYPE html>
        <html>
        <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,sans-serif;color:#333;">
            <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
                <td align="center" style="padding: 40px 0;">
                <table width="600" style="background:#ffffff;border-radius:12px;padding:40px;box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                    <tr>
                    <td align="center" style="padding-bottom:24px;">
                        <img src="https://www.itssafe.com.br/static/global-search2.png" alt="It'sSafe Logo" width="100" style="margin-bottom:16px;">
                        <h2 style="color:#2b2b2b;">Confirm your email</h2>
                    </td>
                    </tr>
                    <tr>
                    <td style="padding:0 30px;text-align:center;">
                        <p>Hi {username}:</p>
                        <p>Click the button below to confirm your email address:</p>
                    </td>
                    </tr>
                    <tr>
                    <td align="center" style="padding:20px;">
                        <a href="https://www.itssafe.com.br/api/user/email/confirmation?token={token}" target="_blank"
                        style="background-color:#4CAF50;color:white;padding:14px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">
                        Confirm Email
                        </a>
                    </td>
                    </tr>
                    <tr>
                    <td style="padding:0 30px;text-align:center;font-size:12px;color:#888;">
                        <p>If you didn’t request this, you can safely ignore this email.</p>
                        <p>© 2025 It'sSafe</p>
                    </td>
                    </tr>
                </table>
                </td>
            </tr>
            </table>
        </body>
        </html>
    """
    data = {
        "dst":dst,
        "subject":"Email validation",
        "message":html_template
    }

    return data