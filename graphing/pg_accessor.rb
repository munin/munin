require 'pg'
require 'pp'
class PgAccessor
  def initialize db_name
    @db_name = db_name
    @db = PGconn.open :host => "localhost", :port => 5432, :dbname => db_name, :user => "munin", :password => "f1r3fly"
  end
 
  def get_planets data_type, planets
    get_info("planet", data_type, get_planet_identifiers(planets))
  end

  def get_galaxies data_type, galaxies
    get_info("galaxy", data_type, get_galaxy_indentifiers(galaxies))
  end

  def get_alliances data_type, alliances 
    get_info("alliance", data_type, get_alliance_indentifiers(alliances))
  end

  def get_galaxy_indentifiers galaxies
    return galaxies.map do |galaxy|
      puts "#{galaxy} on #{@db_name}"
      res = @db.exec "select id from galaxy_dump where tick = (select max_tick()) and x=$1 and y=$2", galaxy.split("\.")
      [galaxy,res[0]['id']]
    end
  end

  def get_alliance_indentifiers alliances
    return alliances.map do |alliance|
      puts "#{alliance} on #{@db_name}"
      res = @db.exec "select id from alliance_dump where tick = (select max_tick()) and name ilike $1", [alliance]
      [alliance,res[0]['id']]
    end
  end

  def get_info type, data_type, identifiers
    scores = { }
    identifiers.each do |id|
      puts "Getting #{data_type} for #{id} of type #{type}"
      query =  "select #{data_type} as result from #{type}_dump where id = $1 order by tick asc"
      puts query
      res = @db.exec query, [id[1]]
      scores[id[0].gsub(/\./, ':')]=res.to_a.map do |r| r['result'].to_i end
    end
    #puts scores 
    return scores
  end

  def get_planet_identifiers planets
    return planets.map do |planet|
      puts "#{planet} on #{@db_name}"
      res = @db.exec "select id from planet_dump where tick = (select max_tick()) and x=$1 and y=$2 and z=$3", planet.split("\.")
      [planet,res[0]['id']]
    end
  end


end
