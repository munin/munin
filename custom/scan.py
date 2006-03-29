import urllib2, re, os, sys, string, psycopg, loadable

class scan:
	def __init__(self, rand_id):

		pid = os.fork()

		if pid:
			return
		else:
			# database connection and cursor
			self.user="andreaja"
		        self.dbname="patools16"
		        self.conn=psycopg.connect("user=%s dbname=%s" % (self.user,self.dbname))
		        self.conn.serialize()
		        self.conn.autocommit()
		        self.c=self.conn.cursor()

			page = urllib2.urlopen('http://game.planetarion.com/showscan.pl?scan_id=' + rand_id).read()

			m = re.search('on (\d+)\:(\d+)\:(\d+) in tick (\d+)', page)
			x = m.group(1)
			y = m.group(2)
			z = m.group(3)
			tick = m.group(4)

			#check to see if we have already added this scan to the database
			query = "SELECT id FROM scan WHERE rand_id=%s and tick=%s"
			self.c.execute(query, (rand_id, tick))
			s=self.c.dictfetchone()
		        if not s:

				p=loadable.planet(x, y, z)
				if p.load_most_recent(self.conn, 0 ,self.c):

					#quickly insert the scan incase someone else pastes it :o
					query = "INSERT INTO scan (tick, pid, scantype, rand_id) VALUES (%s, %s, %s, %s)"
					self.c.execute(query, (tick, p.id, "planet", rand_id))

					#scantype VARCHAR(10) NOT NULL CHECK(scantype in ('planet','structure','technology','unit','news','jgp','fleet'))
					if re.search('Planet Scan', page):
						self.parse_planet(page)
						scantype = "planet"
					elif re.search('Surface Analysis', page):
						self.parse_surface(page)
						scantype = "structure"
					elif re.search('Technology Analysis Scan', page):
						self.parse_technology(page)
						scantype = "technology"
					elif re.search('Unit Scan', page):
						self.parse_unit(page)
						scantype = "unit"
					elif re.search('News Scan', page):
						self.parse_news(page)
						scantype = "news"
					elif re.search('Jumpgate Probe', page):
						self.parse_jumpgate(page)
						scantype = "jgp"

					#finally update the scan setting with the correct scantype
					query = "UPDATE scan (scantype) VALUES (%s) WHERE tick=%s AND rand_id=%s"
					self.c.execute(query, (scantype, tick, rand_id))

			sys.exit(0)

	def parse_news(self, page):
		m = re.search('on (\d+)\:(\d+)\:(\d+) in tick (\d+)', page)
		x = m.group(1)
		y = m.group(2)
		z = m.group(3)
		tick = m.group(4)

	#incoming fleets
	#<td class=left valign=top>Incoming</td><td valign=top>851</td><td class=left valign=top>We have detected an open jumpgate from Tertiary, located at 18:5:11. The fleet will approach our system in tick 855 and appears to have roughly 95 ships.</td>
		for m in re.finditer('<td class=left valign=top>Incoming</td><td valign=top>(\d+)</td><td class=left valign=top>We have detected an open jumpgate from ([^<]+), located at (\d+):(\d+):(\d+). The fleet will approach our system in tick (\d+) and appears to have roughly (\d+) ships.</td>', page):
			newstick = m.group(1)
			fleetname = m.group(2)
			originx = m.group(3)
			originy = m.group(4)
			originz = m.group(5)
			arrivaltick = m.group(6)
			numships = m.group(7)

			print 'Incoming:' + newstick + ':' + fleetname + ':' + originx + ':' + originy + ':' + originz + ':' + arrivaltick + ':' + numships

	#launched attacking fleets
	#<td class=left valign=top>Launch</td><td valign=top>848</td><td class=left valign=top>The Disposable Heroes fleet has been launched, heading for 15:9:8, on a mission to Attack. Arrival tick: 857</td>
		for m in re.finditer('<td class=left valign=top>Launch</td><td valign=top>(\d+)</td><td class=left valign=top>The ([^,]+) fleet has been launched, heading for (\d+):(\d+):(\d+), on a mission to Attack. Arrival tick: (\d+)</td>', page):
			newstick = m.group(1)
			fleetname = m.group(2)
			originx = m.group(3)
			originy = m.group(4)
			originz = m.group(5)
			arrivaltick = m.group(6)

			print 'Attack:' + newstick + ':' + fleetname + ':' + originx + ':' + originy + ':' + originz + ':' + arrivaltick

	#launched defending fleets
	#<td class=left valign=top>Launch</td><td valign=top>847</td><td class=left valign=top>The Ship Collection fleet has been launched, heading for 2:9:14, on a mission to Defend. Arrival tick: 853</td>
		for m in re.finditer('<td class=left valign=top>Launch</td><td valign=top>(\d+)</td><td class=left valign=top>The ([^<]+) fleet has been launched, heading for (\d+):(\d+):(\d+), on a mission to Defend. Arrival tick: (\d+)</td>', page):
			newstick = m.group(1)
			fleetname = m.group(2)
			originx = m.group(3)
			originy = m.group(4)
			originz = m.group(5)
			arrivaltick = m.group(6)

			print 'Defend:' + newstick + ':' + fleetname + ':' + originx + ':' + originy + ':' + originz + ':' + arrivaltick


	#tech report
	#<td class=left valign=top>Tech</td><td valign=top>838</td><td class=left valign=top>Our scientists report that Portable EMP emitters has been finished. Please drop by the Research area and choose the next area of interest.</td>
		for m in re.finditer('<td class=left valign=top>Tech</td><td valign=top>(\d+)</td><td class=left valign=top>Our scientists report that ([^<]+) has been finished. Please drop by the Research area and choose the next area of interest.</td>', page):
			newstick = m.group(1)
			research = m.group(2)

			print 'Tech:' + newstick + ':' + research

	#failed security report
	#<td class=left valign=top>Security</td><td valign=top>873</td><td class=left valign=top>A covert operation was attempted by Ikaris (2:5:5), but our agents were able to stop them from doing any harm.</td>
		for m in re.finditer('<td class=left valign=top>Security</td><td valign=top>(\d+)</td><td class=left valign=top>A covert operation was attempted by ([^<]+) \\((\d+):(\d+):(\d+)\\), but our agents were able to stop them from doing any harm.</td>', page):
			newstick = m.group(1)
			ruler = m.group(2)
			originx = m.group(3)
			originy = m.group(4)
			originz = m.group(5)

			print 'Security:' + newstick + ':' + ruler + ':' + originx + ':' + originy + ':' + originz

	#fleet report
	#<tr bgcolor=#2d2d2d><td class=left valign=top>Fleet</td><td valign=top>881</td><td class=left valign=top><table width=500><tr><th class=left colspan=3>Report of Losses from the Disposable Heroes fighting at 13:10:3</th></tr>
	#<tr><th class=left width=33%>Ship</th><th class=left width=33%>Arrived</th><th class=left width=33%>Lost</th></tr>
	#
	#<tr><td class=left>Syren</td><td class=left>15</td><td class=left>13</td></tr>
	#<tr><td class=left>Behemoth</td><td class=left>13</td><td class=left>13</td></tr>
	#<tr><td class=left>Roach</td><td class=left>6</td><td class=left>6</td></tr>
	#<tr><td class=left>Thief</td><td class=left>1400</td><td class=left>1400</td></tr>
	#<tr><td class=left>Clipper</td><td class=left>300</td><td class=left>181</td></tr>
	#
	#<tr><td class=left>Buccaneer</td><td class=left>220</td><td class=left>102</td></tr>
	#<tr><td class=left>Rogue</td><td class=left>105</td><td class=left>105</td></tr>
	#<tr><td class=left>Marauder</td><td class=left>110</td><td class=left>110</td></tr>
	#<tr><td class=left>Ironclad</td><td class=left>225</td><td class=left>90</td></tr>
	#</table>
	#
	#<table width=500><tr><th class=left colspan=3>Report of Ships Stolen by the Disposable Heroes fighting at 13:10:3</th></tr>
	#<tr><th class=left width=50%>Ship</th><th class=left width=50%>Stolen</th></tr>
	#<tr><td class=left>Roach</td><td class=left>5</td></tr>
	#<tr><td class=left>Hornet</td><td class=left>1</td></tr>
	#<tr><td class=left>Wraith</td><td class=left>36</td></tr>
	#</table>
	#<table width=500><tr><th class=left>Asteroids Captured</th><th class=left>Metal : 37</th><th class=left>Crystal : 36</th><th class=left>Eonium : 34</th></tr></table>
	#
	#</td></tr>

		print 'News: '+x+':'+y+':'+z

	def parse_planet(self, page):
		m = re.search('on (\d*)\:(\d*)\:(\d*) in tick (\d*)', page)
		x = m.group(1)
		y = m.group(2)
		z = m.group(3)
		tick = m.group(4)

		m = re.search('<tr><td class=left>Asteroids</td><td>(\d*)</td><td>(\d*)</td><td>(\d*)</td></tr><tr><td class=left>Resources</td><td>(\d*)</td><td>(\d*)</td><td>(\d*)</td></tr><tr><th>Score</th><td>(\d*)</td><th>Value</th><td>(\d*)</td></tr>', page)
		roid_m = m.group(1)
		roid_c = m.group(2)
		roid_e = m.group(3)
		res_m = m.group(4)
		res_c = m.group(5)
		res_e = m.group(6)
		score = m.group(7)
		value = m.group(8)

		print 'Planet: '+x+':'+y+':'+z

	def parse_surface(self, page):
		m = re.search('on (\d*)\:(\d*)\:(\d*) in tick (\d*)</th></tr><tr><td class=left>Light Factory</td><td>(\d*)</td></tr><tr><td class=left>Medium Factory</td><td>(\d*)</td></tr><tr><td class=left>Heavy Factory</td><td>(\d*)</td></tr><tr><td class=left>Wave Amplifier</td><td>(\d*)</td></tr><tr><td class=left>Wave Distorter</td><td>(\d*)</td></tr><tr><td class=left>Metal Refinery</td><td>(\d*)</td></tr><tr><td class=left>Crystal Refinery</td><td>(\d*)</td></tr><tr><td class=left>Eonium Refinery</td><td>(\d*)</td></tr><tr><td class=left>Research Laboratory</td><td>(\d*)</td></tr><tr><td class=left>Finance Centre</td><td>(\d*)</td></tr><tr><td class=left>Security Centre</td><td>(\d*)</td></tr>', page)
		x = m.group(1)
		y = m.group(2)
		z = m.group(3)
		tick = m.group(4)
		lightfactory = m.group(5)
		medfactory = m.group(6)
		heavyfactory = m.group(7)
		waveamp = m.group(8)
		wavedist = m.group(9)
		metalref = m.group(10)
		crystalref = m.group(11)
		eref = m.group(12)
		reslab = m.group(13)
		finance = m.group(14)
		security = m.group(15)

		print 'Surface: '+x+':'+y+':'+z

	def parse_technology(self, page):
		m = re.search("on (\d*)\:(\d*)\:(\d*) in tick (\d*)</th></tr><tr><th class=left>Space Travel</th><td>(\d*)</td></tr>\\n<tr><th class=left>Infrastructure</th><td>(\d*)</td></tr>\\n<tr><th class=left>Hulls</th><td>(\d*)</td></tr>\\n<tr><th class=left>Waves</th><td>(\d*)</td></tr>\\n<tr><th class=left>Core Extraction</th><td>(\d*)</td></tr>\\n<tr><th class=left>Covert Ops</th><td>(\d*)</td></tr>\\n<tr><th class=left>Asteroid Mining</th><td>(\d*)</td></tr>", page)
		x = m.group(1)
		y = m.group(2)
		z = m.group(3)
		tick = m.group(4)
		travel = m.group(5)
		inf = m.group(6)
		hulls = m.group(7)
		waves = m.group(8)
		core = m.group(9)
		covop = m.group(10)
		mining = m.group(11)

		print 'Technology: '+x+':'+y+':'+z

	def parse_unit(self, page):
		m = re.search('on (\d*)\:(\d*)\:(\d*) in tick (\d*)', page)
		x = m.group(1)
		y = m.group(2)
		z = m.group(3)
		tick = m.group(4)

		harpy = gryphon = phoenix = chimera = pegasus = barghest = syren = wyvern = dragon = ziz = leviathan = behemoth = 0
		spider = beetle = viper = recluse = blackwidow = scarab = tarantula = roach = mantis = mosquito = hornet = termite = 0
		phantom = vsharrak = fireblade = arrowhead = tzen = ghost = peacekeeper = wraith = broadsword = dagger = sabre = predator = 0
		interceptor = cutlass = thief = assassin = clipper = buccaneer = rogue = marauder = pirate = privateer = ironclad = galleon = 0

		m = re.search('Harpy</td><td>(\d*)</td>', page)
		if m:
			harpy = m.group(1)
		m = re.search('Gryphon</td><td>(\d*)</td>', page)
		if m:
			gryphon = m.group(1)
		m = re.search('Phoenix</td><td>(\d*)</td>', page)
		if m:
			phoenix = m.group(1)
		m = re.search('Chimera</td><td>(\d*)</td>', page)
		if m:
			chimera = m.group(1)
		m = re.search('Pegasus</td><td>(\d*)</td>', page)
		if m:
			pegasus = m.group(1)
		m = re.search('Barghest</td><td>(\d*)</td>', page)
		if m:
			barghest = m.group(1)
		m = re.search('Syren</td><td>(\d*)</td>', page)
		if m:
			syren = m.group(1)
		m = re.search('Wyvern</td><td>(\d*)</td>', page)
		if m:
			wyvern = m.group(1)
		m = re.search('Dragon</td><td>(\d*)</td>', page)
		if m:
			dragon = m.group(1)
		m = re.search('Ziz</td><td>(\d*)</td>', page)
		if m:
			ziz = m.group(1)
		m = re.search('Leviathan</td><td>(\d*)</td>', page)
		if m:
			leviathan = m.group(1)
		m = re.search('Behemoth</td><td>(\d*)</td>', page)
		if m:
			behemoth = m.group(1)

		m = re.search('Spider</td><td>(\d*)</td>', page)
		if m:
			spider = m.group(1)
		m = re.search('Beetle</td><td>(\d*)</td>', page)
		if m:
			beetle = m.group(1)
		m = re.search('Viper</td><td>(\d*)</td>', page)
		if m:
			viper = m.group(1)
		m = re.search('Recluse</td><td>(\d*)</td>', page)
		if m:
			recluse = m.group(1)
		m = re.search('Black Widow</td><td>(\d*)</td>', page)
		if m:
			blackwidow = m.group(1)
		m = re.search('Scarab</td><td>(\d*)</td>', page)
		if m:
			scarab = m.group(1)
		m = re.search('Tarantula</td><td>(\d*)</td>', page)
		if m:
			tarantula = m.group(1)
		m = re.search('Roach</td><td>(\d*)</td>', page)
		if m:
			roach = m.group(1)
		m = re.search('Mantis</td><td>(\d*)</td>', page)
		if m:
			mantis = m.group(1)
		m = re.search('Mosquito</td><td>(\d*)</td>', page)
		if m:
			mosquito = m.group(1)
		m = re.search('Hornet</td><td>(\d*)</td>', page)
		if m:
			hornet = m.group(1)
		m = re.search('Termite</td><td>(\d*)</td>', page)
		if m:
			termite = m.group(1)

		m = re.search('Phantom</td><td>(\d*)</td>', page)
		if m:
			phantom = m.group(1)
		m = re.search('Vsharrak</td><td>(\d*)</td>', page)
		if m:
			vsharrak = m.group(1)
		m = re.search('Fireblade</td><td>(\d*)</td>', page)
		if m:
			fireblade = m.group(1)
		m = re.search('Arrowhead</td><td>(\d*)</td>', page)
		if m:
			arrowhead = m.group(1)
		m = re.search('Tzen</td><td>(\d*)</td>', page)
		if m:
			tzen = m.group(1)
		m = re.search('Ghost</td><td>(\d*)</td>', page)
		if m:
			ghost = m.group(1)
		m = re.search('Peacekeeper</td><td>(\d*)</td>', page)
		if m:
			peacekeeper = m.group(1)
		m = re.search('Wraith</td><td>(\d*)</td>', page)
		if m:
			wraith = m.group(1)
		m = re.search('Broadsword</td><td>(\d*)</td>', page)
		if m:
			broadsword = m.group(1)
		m = re.search('Dagger</td><td>(\d*)</td>', page)
		if m:
			dagger = m.group(1)
		m = re.search('Sabre</td><td>(\d*)</td>', page)
		if m:
			sabre = m.group(1)
		m = re.search('Predator</td><td>(\d*)</td>', page)
		if m:
			predator = m.group(1)

		m = re.search('Interceptor</td><td>(\d*)</td>', page)
		if m:
			interceptor = m.group(1)
		m = re.search('Cutlass</td><td>(\d*)</td>', page)
		if m:
			cutlass = m.group(1)
		m = re.search('Thief</td><td>(\d*)</td>', page)
		if m:
			thief = m.group(1)
		m = re.search('Assassin</td><td>(\d*)</td>', page)
		if m:
			assassin = m.group(1)
		m = re.search('Clipper</td><td>(\d*)</td>', page)
		if m:
			clipper = m.group(1)
		m = re.search('Buccaneer</td><td>(\d*)</td>', page)
		if m:
			buccaneer = m.group(1)
		m = re.search('Rogue</td><td>(\d*)</td>', page)
		if m:
			rogue = m.group(1)
		m = re.search('Marauder</td><td>(\d*)</td>', page)
		if m:
			marauder = m.group(1)
		m = re.search('Pirate</td><td>(\d*)</td>', page)
		if m:
			pirate = m.group(1)
		m = re.search('Privateer</td><td>(\d*)</td>', page)
		if m:
			privateer = m.group(1)
		m = re.search('Ironclad</td><td>(\d*)</td>', page)
		if m:
			ironclad = m.group(1)
		m = re.search('Galleon</td><td>(\d*)</td>', page)
		if m:
			galleon = m.group(1)

		print harpy

		print 'Unit: '+x+':'+y+':'+z

	def parse_jumpgate(self, page):
		m = re.search('on (\d+)\:(\d+)\:(\d+) in tick (\d+)', page)
		x = m.group(1)
		y = m.group(2)
		z = m.group(3)
		tick = m.group(4)
		# <td class=left>Origin</td><td class=left>Mission</td><td>Fleet</td><td>ETA</td><td>Fleetsize</td>
		# <td class=left>13:10:5</td><td class=left>Attack</td><td>Gamma</td><td>5</td><td>265</td>

		for m in re.finditer('<td class=left>(\d+)\:(\d+)\:(\d+)</td><td class=left>([^<]+)</td><td>([^<]+)</td><td>(\d+)</td><td>(\d+)</td>', page):
			originx = m.group(1)
			originy = m.group(2)
			originz = m.group(3)
			mission = m.group(4)
			fleet = m.group(5)
			eta = m.group(6)
			fleetsize = m.group(7)
		
		print 'Jumpgate: '+x+':'+y+':'+z