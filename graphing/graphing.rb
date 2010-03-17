#!/usr/bin/env ruby

require 'rubygems'
require 'gruff'
require 'utils/round'
require 'pg'

rounds = { }

File.open "tmp/graphing.txt" do |infile|
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

db = PGconn.open :host => "localhost", :port => 5432, :dbname => 'patools21', :user => "munin", :password => "f1r3fly"
res = db.exec "select id from planet_dump where tick = (select max_tick()) and x=$1 and y=$2 and z=$3", round['Round 21'].planets[0].split("\.")
pp res[0]
#pp rounds
=begin
g = Gruff::Line.new
g.title = "My Graph" 

g.data("Apples", [1, 2, 3, 4, 4, 3])
g.data("Oranges", [4, 8, 7, 9, 8, 9])
g.data("Watermelon", [2, 3, 1, 5, 6, 8])
g.data("Peaches", [9, 9, 10, 8, 7, 9])

g.labels = {0 => '2003', 2 => '2004', 4 => '2005'}

g.write('my_fruity_graph.png')

=end
