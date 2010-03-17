require 'pp'

class Round
  attr_accessor :name,:alliances,:galaxies,:planets
  def alliances= a
    @alliances = a.split("/")
  end

  def galaxies= g
    @galaxies = g.split("/")
  end

  def planets= p
    @planets = p.split("/")
  end
  def to_s 
    "Alliances:" + @alliances.join(", ") + "; Galaxies: " + @galaxies.join(", ") + "; Planets: " + @planets.join(", ")
  end
end

