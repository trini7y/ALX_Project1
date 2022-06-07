#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
from email.policy import default
import os
import sys
from distutils.command.config import config
import json
import dateutil.parser
import babel
from flask import (
    abort, 
    jsonify, 
    render_template,
    request, 
    flash, 
    redirect, 
    url_for
  )
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from datetime import datetime
from models import ( 
    Venue, 
    Show, 
    Artist, 
    app, 
    moment, 
    db, 
    migrate
  )
from forms import ShowForm, ArtistForm, VenueForm

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#






# TODO: connect to a local postgresql database;

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  try:
      data = []
      venues = db.session.query(Venue.city, Venue.state).distinct().all()
      for sc in venues:
        state_city = Venue.query.filter_by(state=sc.state).filter_by(city=sc.city).all()
        subdata = []
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')

        for venue in state_city:
          subdata.append({
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_show': Show.query.filter(db.and_(Show.created_time > current_time, Show.venue_id == venue.id)).count()
          })
        data.append({
          'city': sc.city,
          'state': sc.state,
          'venues':subdata
        })
  except Exception as e:
      print(e)
  finally:
    return render_template('pages/venues.html', areas=data )
  
  
def get_search_result(search_word, schema):
  try:
    data = schema.query.filter(db.func.lower(schema.name).like(
      f'%{search_word.lower()}%')).order_by('name').all()
    return data
  except Exception as e:
     print(e)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  try:
    data = get_search_result(request.form['search_term'], Venue)
    vens = []
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    for venue in data:
       vens.append({
        'id': venue.id,
        'name': venue.name,
        'num_upcoming_show': Show.query.filter(db.and_(Show.created_time > current_time, Show.venue_id == venue.id)).count()
       })
    response = {
       'count': len(data),
       'data': vens
    }
  except:
    flash('Sorry, something went wrong while searching. Please try again', category="error")
  
  finally:
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

 

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data = {}
  try:
    venue = Venue.query.filter(Venue.id == venue_id).first()

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    past_events = db.session.query(Show).join(Artist).filter(
        db.and_(Show.created_time < current_time, Show.venue_id == venue_id)).all()
    past_shows = []
    for artist in past_events:
        past_show = {
          'artist_id':artist.id,
          'artist_name': artist.name,
          'artist_image_link': artist.image_link,
          'start_time': str(Show.current_date)
        }
        past_shows.append( past_show )
    
    upcoming_events = db.session.query(Show).join(Artist).filter(
        db.and_(Show.created_time > current_time, Show.venue_id == venue_id)).all()
    upcoming_shows = []
    for artist in upcoming_events:
        upcoming_show = {
          'artist_id':artist.id,
          'artist_name': artist.name,
          'artist_image_link': artist.image_link,
          'start_time': str(Show.current_date)
        }
        upcoming_shows.append( upcoming_show )

    data = {
        'id': venue.id,
        'name': venue.name,
        'genres': venue.genres,
        'address': venue.address,
        'city': venue.city,
        'state': venue.state,
        'phone': venue.phone,
        'website': venue.website_link,
        'facebook_link':venue.facebook_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_desc,
        'image_link': venue.image_link,
        'past_shows':past_shows,
        'upcoming_shows':upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count':len(upcoming_shows)
    }
   
  except:
      flash('Sorry, there is no info regarding' + venue.id, category='info')
  
  finally:
      return render_template('pages/show_venue.html', venue=data)
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = VenueForm(request.form)
  try:
    if form.validate():
      venue = Venue(name=request.form['name'],  city=request.form['city'], state=request.form['state'], address=request.form['address'], phone=request.form['phone'], genres=request.form.getlist('genres', type=str), 
      image_link=request.form['image_link'], facebook_link=request.form['facebook_link'], seeking_talent=request.form.get('seeking_talent', type=bool), website_link=request.form['website_link'], 
      seeking_desc=request.form['seeking_description'])
      # on successful db insert, flash success
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # on successful db insert, flash success
  except:
    # You only want to print the errors since fail on validate
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name']  + ' could not be listed.')
  finally:
      db.session.close()
      return render_template('pages/home.html', form=form)
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
 

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    Venue.query.filter(Venue.id == venue_id).delete()
    db.session.commit()
    flash('Venue with id' + venue_id + 'was deleted succesfully')
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  except:
    flash('Venue with id' + venue_id + 'could not be deleted', category='error')
    db.session.rollback()
    abort(500)
  finally:
    db.session.close()
    return jsonify({"homeUrl": '/'})

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = []
  artists = db.session.query(Artist.id, Artist.name).all()
  for artist in artists:
    data.append({
      'id':artist.id,
      'name': artist.name
    })
    
  return render_template('pages/artists.html', artists=data)



@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response = {}
  try:
    data = get_search_result(request.form['search_term'], Artist)
    artists = []
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    for artist in data:
      artists.append({
        'id': artist.id,
        'name':artist.name,
        'num_upcoming_show': Show.query.filter(db.and_(Show.created_time > current_time, Show.artist_id == artist.id)).count()
      })
    response = {
      'count':len(data),
      'data':artists
    }
      
  except:
      flash('Sorry, something went wrong while searching. Please try again', category="error")
   
  finally:
      return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # Shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  #artist_details = db.session.query(Artist).all()
  data = {}
  try:
    artist = Artist.query.filter(Artist.id == artist_id).first()
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    past_events = db.session.query(Show).join(Venue).filter(
        db.and_(Show.created_time < current_time, Show.artist_id == artist_id)).all()
    past_shows = []
    for venue in past_events:
        past_show = {
          'venue_id':venue.id,
          'venue_name': venue.name,
          'venue_image_link': venue.image_link,
          'start_time': str(Show.current_date)
        }
        past_shows.append( past_show )
    
    upcoming_events = db.session.query(Show).join(Venue).filter(
        db.and_(Show.created_time > current_time, Show.artist_id == artist_id)).all()
    upcoming_shows = []
    for venue in upcoming_events:
        upcoming_show = {
          'venue_id':venue.id,
          'venue_name': venue.name,
          'venue_image_link': venue.image_link,
          'start_time': str(Show.current_date)
        }
        upcoming_shows.append( upcoming_show )

    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website_link,
        'facebook_link':artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_desc,
        'image_link': artist.image_link,
        'past_shows':past_shows,
        'upcoming_shows':upcoming_shows,
        'past_shows_count': len(past_shows),
        'upcoming_shows_count':len(upcoming_shows)
    }
   
  except:
      flash('Sorry, there is no info regarding' + artist.id, category='info')
  
  finally:
      return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    try:
        data = Artist.query.filter(Artist.id == artist_id).first()
        artist_form = ArtistForm(name=data.name, city=data.city, 
                            state=data.state, phone=data.phone,
                            image_link=data.image_link, 
                            genres=data.genres,
                            facebook_link=data.facebook_link,
                            website_link=data.website_link,
                            seeking_venue=data.seeking_venue, 
                            seeking_description=data.seeking_desc
        )
    except:
        flash(f"Sorry, unable to load up the Artist Edit form.", category="error")
        abort(500)
    finally:
        return render_template('forms/edit_artist.html', form=artist_form, artist=data) 

  # TODO: populate form with fields from artist with ID <artist_id>
  

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)

  if form.validate():
      try:
        data = Artist.query.filter(Artist.id == artist_id).first() 
        data.name = request.form['name']
        data.city = request.form['city']
        data.genres = request.form.getlist('genres', type=str)
        data.state = request.form['state']
        data.phone = request.form['phone']
        data.image_link = request.form['image_link']
        data.facebook_link = request.form['facebook_link']
        data.website_link = request.form['website_link']
        data.seeking_venue = request.form.get('seeking_venue', type=bool)
        data.seeking_desc = request.form['seeking_description']
        db.session.commit()
        flash('You have successfully updated your information')
      except:
        flash('Sorry, the artist could not be updated', category ='error')
        db.session.rollback()
      finally:
        db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))
  
  

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  try:
    data = Venue.query.filter(Venue.id == venue_id).first()
    venue_form = VenueForm(name=data.name, city=data.city, 
                            state=data.state, 
                            address=data.address,
                            phone=data.phone,
                            image_link=data.image_link, 
                            genres=data.genres,
                            facebook_link=data.facebook_link,
                            website_link=data.website_link,
                            seeking_talent=data.seeking_talent, 
                            seeking_description=data.seeking_desc
        )
  except:
      flash(f"Sorry, unable to load up the Venue Edit form.", category="error")
      abort(500)
  finally:
      return render_template('forms/edit_venue.html', form=venue_form, venue=data) 
  # TODO: populate form with values from venue with ID <venue_id>

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  if form.validate():
      try:
        data = Venue.query.filter(Venue.id == venue_id).first() 
        data.name = request.form['name']
        data.city = request.form['city']
        data.genres = request.form.getlist('genres', type=str)
        data.address = request.form['address']
        data.state = request.form['state']
        data.phone = request.form['phone']
        data.image_link = request.form['image_link']
        data.facebook_link = request.form['facebook_link']
        data.website_link = request.form['website_link']
        data.seeking_venue = request.form.get('seeking_venue', type=bool)
        data.seeking_desc = request.form['seeking_description']
        db.session.commit()
        flash('You have successfully updated your information')
      except:
        flash('Sorry, the venue could not be updated', category ='error')
        db.session.rollback()
      finally:
        db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm(request.form)
    try:
      if form.validate():
        artist = Artist(name=request.form['name'],  city=request.form['city'], state=request.form['state'], phone=request.form['phone'], genres=request.form.getlist('genres', type=str), 
        image_link=request.form['image_link'], facebook_link=request.form['facebook_link'], seeking_venue=request.form.get('seeking_venue', type=bool), website_link=request.form['website_link'], 
        seeking_desc=request.form['seeking_description'])
        # on successful db insert, flash success
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    except:
    # You only want to print the errors since fail on validate
      db.session.rollback()
      flash('An error occurred. Artist ' + request.form['name']  + ' could not be listed.')
    finally:
      db.session.close()
    return render_template('pages/home.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data=[{
    "venue_id": 1,
    "venue_name": "The Musical Hop",
    "artist_id": 4,
    "artist_name": "Guns N Petals",
    "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    "start_time": "2019-05-21T21:30:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 5,
    "artist_name": "Matt Quevedo",
    "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    "start_time": "2019-06-15T23:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-01T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-08T20:00:00.000Z"
  }, {
    "venue_id": 3,
    "venue_name": "Park Square Live Music & Coffee",
    "artist_id": 6,
    "artist_name": "The Wild Sax Band",
    "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    "start_time": "2035-04-15T20:00:00.000Z"
  }]
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new Show listing form
  # TODO: insert form data as a new Show record in the db, instead

  # on successful db insert, flash success
  flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
# if __name__ == '__main__':
#     app.run()

# Or specify port manually:

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

