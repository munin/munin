#!/usr/bin/env ruby

require 'rubygems'
require 'gruff'
require 'graphing/round'
require 'graphing/pg_accessor.rb'

def draw_graph graph_data
  g = Gruff::Line.new
  g.theme = {
    :colors => ['#ff6600', '#3bb000', '#1e90ff', '#efba00', '#0aaafd'],
    :marker_color => '#000',
    :font_color => "grey",
    :background_colors => ["#0B243B", "#0B243B"]
  }
 
  g.title = "Round #{graph_data.round_number} #{graph_data.entity_type} #{graph_data.data_type}" 
  graph_data.data.each do |key, value|
    g.data(key, value )
  end
  
  # TODO: min_round_tick
  g.labels = { (500-36) => "500", (1000-36) => "1000"}
  g.write("Round #{graph_data.round_number}_#{graph_data.entity_type}_#{graph_data.data_type}.png")
end

def create_graph graph_data
  graph_data.data = PgAccessor.new(db_name).send("get_#{graph_data.entity_type}",graph_data.data_type,rounds[round].send(graph_data.entity_type))
  draw_graph graph_data
end

class GraphData
  attr_accessor :round_number, :data, :entity_type, :data_type
end


def process rounds 
  #rounds.keys.each do |round|
  ["Round 21"].each do |round|
    gdata = GraphData.new
    gdata.round_number = round.split(' ')[1]
    puts "Fetching data for #{gdata.round_number}"
    db_name = "patools#{gdata.round_number}" 
    ["planets","alliances","galaxies"].each do |var|
      gd = gdata.clone
      gd.entity_type = var
      puts "Iterating for #{gd.entity_type} on #{gd.round_number}"
      [:score, :size, :value].each do |data_type|
        if(data_type == :value and gd.entity_type == "alliances") then
          gd.data_type = data_type
          create_graph gd
        end
      end
    end
  end
end

def read_rounds_from_file filename
  rounds = { }  
  File.open filename do |infile|
    counter = 0
    while (line = infile.gets)
      line.chomp!
      if line =~ /^Round \d+$/i
        current = line
        rounds[current] = Round.new
      end
      if line =~ /^\D+/
        rounds[current].alliances = line
      end
      if line =~ /^\d+\.\d+\//
        rounds[current].galaxies = line
      end
      if line =~ /\d+\.\d+\.\d+\//
        rounds[current].planets = line
      end
      puts "#{counter}: #{line}"
      counter = counter + 1
    end
  end
end

process(read_rounds_from_file("graphing/graphing.txt"))

=begin
db = PGconn.open :host => "localhost", :port => 5432, :dbname => 'patools21', :user => "munin", :password => "f1r3fly"
res = db.exec "select id from planet_dump where tick = (select max_tick()) and x=$1 and y=$2 and z=$3", round['Round 21'].planets[0].split("\.")
pp res[0]
#pp rounds

g = Gruff::Line.new
g.title = "My Graph" 

g.data("Apples", [1, 2, 3, 4, 4, 3])
g.data("Oranges", [4, 8, 7, 9, 8, 9])
g.data("Watermelon", [2, 3, 1, 5, 6, 8])
g.data("Peaches", [9, 9, 10, 8, 7, 9])

g.labels = {0 => '2003', 2 => '2004', 4 => '2005'}

g.write('my_fruity_graph.png')

=end

