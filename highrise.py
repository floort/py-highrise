#!/usr/bin/env python

from xml.dom.minidom import parseString
import httplib2


class Highrise(object):
	""" Access the Highrise database.
	"""
	
	def __init__(self, project, token):
		self.base_url = "https://%s.highrisehq.com" % (project)
		self.token = token
	
	def __getattr__(self, name):
		""" Customise attribute lookup.
		"""
		if name == "tags":
			return self.get_tags
		else:
			raise AttributeError


	def _get_page(self, page, method = "GET", data = False):
		http = httplib2.Http()
		http.add_credentials(self.token, "x")
		if not data:
			res = http.request(self.base_url + page, method)
		else:
			res = http.request(self.base_url + page, method, data,
				headers = {"content-type":"application/xml"})
		if res[0]["status"] == "200":
			return res[1]
		else:
			print "HTTP STATUS:", res[0]["status"]
			return res[1]
			return False

	def _parse_email_address(self, email_address):
		e = {}
		tags = ["id", "address", "location"]
		for t in tags:
			nodes = email_address.getElementsByTagName(t)[0].childNodes
			if nodes:	
				e[t] = nodes[0].data
		return e

	def _parse_phone_number(self, phone_number):
		p = {}
		tags = ["id", "number", "location"]
		for t in tags:
			nodes = phone_number.getElementsByTagName(t)
			if nodes:
				nodes = nodes[0].childNodes
			if nodes:
				p[t] = nodes[0].data
		return p

	def _parse_address(self, address):
		a = {}
		tags = ["id", "city", "country", "state", "street", "zip",
				"location"]
		for t in tags:
			nodes = address.getElementsByTagName(t)
			if nodes:
				nodes = nodes[0].childNodes
			if nodes:
				a[t] = nodes[0].data
		return a

	def _parse_instant_messenger(self, instant_messenger):
		i = {}
		tags = ["id", "address", "protocol", "location"]
		for t in tags:
			nodes = instant_messenger.getElementsByTagName(t)
			if nodes:
				nodes = nodes[0].childNodes
			if nodes:
				i[t] = nodes[0].data
		return i

	def _parse_web_address(self, web_address):
		w = {}
		tags = ["id", "url", "location"]
		for t in tags:
			nodes = web_address.getElementsByTagName(t)
			if nodes:
				nodes = nodes[0].childNodes
			if nodes:
				w[t] = nodes[0].data
		return w

	def _parse_contact_data(self, contact_data):
		c = {}
		c["email-addresses"] = []
		for email_address in contact_data.getElementsByTagName("email-address"):
			c["email-addresses"].append(self._parse_email_address(email_address))
		c["phone-numbers"] = []
		for phone_number in contact_data.getElementsByTagName("phone-number"):
			c["phone-numbers"].append(self._parse_phone_number(phone_number))
		c["addresses"] = []
		for address in contact_data.getElementsByTagName("address"):
			c["addresses"].append(self._parse_address(address))
		c["instant-messengers"] = []
		for instant_messenger in contact_data.getElementsByTagName("instant-messenger"):
			c["instant-messengers"].append(self._parse_instant_messenger(instant_messenger))
		c["web-addresses"] = []
		for web_address in contact_data.getElementsByTagName("web-addresses"):
			c["web-addresses"].append(self._parse_web_address(web_address))

		return c

	def _parse_person(self, person):
		p = {}
		tags = ["id", "first-name", "last-name", "title", "background",
			"company-id", "created-at", "updated-at", "visible-to",
			"owner-id", "group-id", "author-id"]
		for t in tags:
			nodes = person.getElementsByTagName(t)[0].childNodes
			if nodes:
				p[t] = nodes[0].data
		p["contact-data"] = self._parse_contact_data(
								person.getElementsByTagName("contact-data")[0])

		return p
	
	def _tags(self, tag, content = ""):
		return "<%s>%s</%s>" % (tag, content, tag)
	
	def _gen_person_xml(self, **kw):
		xml = "<person>"
		if kw.has_key("first_name"):
			xml += self._tags("first-name", kw["first_name"])
		if kw.has_key("last_name"):
			xml += self._tags("last-name", kw["last_name"])
		if kw.has_key("title"):
			xml += self._tags("title", kw["title"])
		if kw.has_key("company_name"):
			xml += self._tags("company-name", kw["company_name"])
		
		contact = ""
		if kw.has_key("email_address"):
			contact += self._tags("email-adresses", 
				self._tags("email-address",
					self._tags("address", kw["email_address"]) + \
					self._tags("location", "Personal")
				)	
			)
		if kw.has_key("phone_number"):
			contact += self._tags("phone-numbers", 
				self._tags("phone-number", 
					self._tags("number", kw["phone_number"]) + \
					self._tags("location", "Personal")
				)
			)
		if contact:
			xml += self._tags("contact-data", contact)
		xml += "</person>"
		return xml
		
	def put_person(self, xml):
		xml = self._get_page("/people.xml", "POST", xml)
		
	def get_tags(self):
		""" Return a dictionary with id:name pairs containing all tags.
		"""
		taglist = {}
		xml = self._get_page("/tags.xml")
		if not xml:
			return False
		dom = parseString(xml)
		tags = dom.getElementsByTagName("tag")
		for tag in tags:
			id = tag.getElementsByTagName("id")[0]
			name = tag.getElementsByTagName("name")[0]
			taglist[int(id.childNodes[0].data)] = name.childNodes[0].data
		return taglist

	def attach_tag(self, type, id, name):
		"""Attach a tag called name to object of type with id"""
		xml = self._get_page("/%s/%d/tags.xml" %(type, id), 
			"POST", "<name>%s</name>" % (name))
		return xml



	def get_parties(self, tag_id):
		
		parties = []
		xml = self._get_page("/tags/%d.xml" % (int(tag_id)))

		dom = parseString(xml)
		for person in dom.getElementsByTagName("person"):
			parties.append(self._parse_person(person))
		return parties


