#!/usr/bin/env ruby

require 'rubygems'
require 'gruff'
require 'graphing/round'
require 'graphing/pg_accessor.rb'


rounds = { }

File.open "graphing/graphing.txt" do |infile|
  counter = 0
  while (line = infile.gets)
    line.chomp!
    if line =~ /^Round \d+$/
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
planets = PgAccessor.new('patools21').get_planets(rounds['Round 21'].planets)
g = Gruff::Line.new
g.title = "My Round 21 Planet Graph" 
planets.each do |key, value|
  g.data(key, value )
end
g.write('my_fruity_graph.png')

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
