#!/usr/bin/env ruby

require 'rubygems'
require 'gruff'
require 'graphing/round'
require 'graphing/pg_accessor.rb'


def digits i
  count = 0
  while i > 0
    count += 1
    i /= 10
  end
  return count
end

def max_from_all data
  max = 0
  data.each do |key, value| 
    valmax = value.max
    if valmax > max
      max = valmax
    end
  end
  return max
end

def get_increment data
  max = max_from_all data
  puts "Max #{max}"
  order = 10 ** (digits(max) - 1)
  increment = (order * (max/order)) / 10 
  return increment
end

def max_value data
  max = max_from_all data
  order = 10 ** (digits(max) - 1)
  return order * ((max/order)+1)
end
def draw_graph graph_data
  g = Gruff::Line.new(1024)
  y_increment = get_increment graph_data.data
  puts "y axis increment #{y_increment}"
  g.y_axis_increment = y_increment
  g.theme = {
    #:colors => ['#ff6600', '#3bb000', '#1e90ff', '#efba00', '#0aaafd'],
    :colors => %w(yellow red blue green purple),
    :marker_color => '#000',
    :font_color => "grey",
    :background_colors => ["#0B243B", "#0B243B"]
  }
 
  g.title = "Round #{graph_data.round_number} #{graph_data.entity_type} #{graph_data.data_type}" 
  graph_data.data.each do |key, value|
    g.data(key, value )
  end
  
  # TODO: min_round_tick
  g.labels = { (250-36) => 250, (500-36) => "500", (750-36) => "750", (1000-36) => "1000"}
  g.minimum_value = 0
  #g.maximum_value = y_increment * 11 
  g.write("Round_#{graph_data.round_number}_#{graph_data.entity_type}_#{graph_data.data_type}.png")
end

def create_graph graph_data, round
  graph_data.data = PgAccessor.new(graph_data.db_name).send("get_#{graph_data.entity_type}",graph_data.data_type,round.send(graph_data.entity_type))
  draw_graph graph_data
end

class GraphData
  attr_accessor :round_number, :data, :entity_type, :data_type, :db_name
end

def graph_information gd, round, graph_types
  graph_types.each do |data_type|
    if not (data_type == :value and gd.entity_type == "alliances") then
      gd.data_type = data_type
      create_graph gd, round
    end
  end

end


def process rounds 
  rounds.keys.each do |round|
  #["Round 21"].each do |round|
    gdata = GraphData.new
    gdata.round_number = round.split(' ')[1]
    puts "Fetching data for #{gdata.round_number}"
    gdata.db_name = "patools#{gdata.round_number}" 
    ["planets","alliances","galaxies"].each do |var|
      gd = gdata.clone
      gd.entity_type = var
      puts "Iterating for #{gd.entity_type} on #{gd.round_number}"
      graph_information gd, rounds[round], [:score, :size, :value]
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
  return rounds
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

