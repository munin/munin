require 'pg'

class PgAccessor
  def initialize db_name
    @db = PGconn.open :host => "localhost", :port => 5432, :dbname => db_name, :user => "munin", :password => "f1r3fly"
  end
 
  def get_planets planets
    get_planet_info(get_planet_identifiers(planets))
  end

  def get_planet_info identifiers
    scores = { }
    identifiers.each do |planet|
      res = @db.exec "select score from planet_dump where id = $1", [planet[1]]
      scores[planet[0].gsub(/\./, ':')]=res.to_a.map do |r| r['score'].to_i end
    end
    return scores
  end

  def get_planet_identifiers planets
    return planets.map do |planet|
      res = @db.exec "select id from planet_dump where tick = (select max_tick()) and x=$1 and y=$2 and z=$3", planet.split("\.")
      [planet,res[0]['id']]
    end
  end


end
