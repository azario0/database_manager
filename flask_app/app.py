from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://YOUR_LOGIN:YOUR_PASSWORD@localhost/world'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Model
class Country(db.Model):
    __tablename__ = 'country'
    
    CountryName = db.Column(db.String(100), primary_key=True)
    CapitalName = db.Column(db.String(100))
    CapitalLatitude = db.Column(db.Float)
    CapitalLongitude = db.Column(db.Float)
    CountryCode = db.Column(db.String(3))
    ContinentName = db.Column(db.String(100))

# Routes
@app.route('/api/countries', methods=['GET'])
def get_all_countries():
    """Get all countries with optional pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        countries = Country.query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'countries': [{
                'country_name': country.CountryName,
                'capital_name': country.CapitalName,
                'capital_latitude': country.CapitalLatitude,
                'capital_longitude': country.CapitalLongitude,
                'country_code': country.CountryCode,
                'continent_name': country.ContinentName
            } for country in countries.items],
            'total_pages': countries.pages,
            'current_page': page,
            'total_records': countries.total
        })
    except Exception as e:
        logger.error(f"Error in get_all_countries: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/countries/search', methods=['GET'])
def search_country():
    """Search countries by name (partial match supported)"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
            
        countries = Country.query.filter(Country.CountryName.ilike(f'%{query}%')).all()
        
        return jsonify({
            'results': [{
                'country_name': country.CountryName,
                'capital_name': country.CapitalName,
                'capital_latitude': country.CapitalLatitude,
                'capital_longitude': country.CapitalLongitude,
                'country_code': country.CountryCode,
                'continent_name': country.ContinentName
            } for country in countries],
            'count': len(countries)
        })
    except Exception as e:
        logger.error(f"Error in search_country: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/countries/continent/<continent_name>', methods=['GET'])
def get_countries_by_continent(continent_name):
    """Get all countries in a specific continent"""
    try:
        countries = Country.query.filter_by(ContinentName=continent_name).all()
        return jsonify({
            'continent': continent_name,
            'countries': [{
                'country_name': country.CountryName,
                'capital_name': country.CapitalName,
                'country_code': country.CountryCode
            } for country in countries],
            'count': len(countries)
        })
    except Exception as e:
        logger.error(f"Error in get_countries_by_continent: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/countries/<country_name>', methods=['GET'])
def get_country_details(country_name):
    """Get detailed information about a specific country"""
    try:
        country = Country.query.filter_by(CountryName=country_name).first()
        
        if not country:
            return jsonify({'error': 'Country not found'}), 404
            
        return jsonify({
            'country_name': country.CountryName,
            'capital_name': country.CapitalName,
            'capital_latitude': country.CapitalLatitude,
            'capital_longitude': country.CapitalLongitude,
            'country_code': country.CountryCode,
            'continent_name': country.ContinentName
        })
    except Exception as e:
        logger.error(f"Error in get_country_details: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/continents', methods=['GET'])
def get_continents():
    """Get list of all continents and their country count"""
    try:
        continents = db.session.query(
            Country.ContinentName,
            db.func.count(Country.CountryName).label('country_count')
        ).group_by(Country.ContinentName).all()
        
        return jsonify({
            'continents': [{
                'name': continent.ContinentName,
                'country_count': continent.country_count
            } for continent in continents]
        })
    except Exception as e:
        logger.error(f"Error in get_continents: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get general statistics about the database"""
    try:
        total_countries = Country.query.count()
        continents_count = db.session.query(Country.ContinentName).distinct().count()
        
        return jsonify({
            'total_countries': total_countries,
            'total_continents': continents_count,
            'last_updated': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True)