#!/usr/bin/env python

# Copyright (c) 2009, Floor Terra <floort@gmail.com>
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.


from xml.dom.minidom import parseString
import httplib2


class Comment(object):
	def __init__(self, id=False):
		self.id = None
		self.parent_id = None
		self.author_id = None
		self.created_at = None
		self.body = None
		
		if id:
			self.load_from_id(id)

	def __unicode__(self):
		return self.body

	def load_from_id(self, id):
		pass
	
	def save(self):
		pass





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
		return (res[0]["status"], res[1])

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
		if kw.has_key("visible_to"):
			xml += self._tags("visible-to", kw["visible_to"])
		if kw.has_key("owner_id"):
			xml += "<owner-id type=\"integer\">%d</owner-id>" % (kw["owner_id"])
		if kw.has_key("group_id"):
			xml += "<group-id type=\"integer\">%d</group-id>" % (kw["group_id"])
		
		contact = ""
		if kw.has_key("email_address"):
			contact += self._tags("email-addresses", 
				self._tags("email-address",
					self._tags("address", kw["email_address"]) + \
					self._tags("location", "Home")
				)	
			)
		if kw.has_key("phone_number"):
			contact += self._tags("phone-numbers", 
				self._tags("phone-number", 
					self._tags("number", kw["phone_number"]) + \
					self._tags("location", "Home")
				)
			)
		if contact:
			xml += self._tags("contact-data", contact)
		xml += "</person>"
		return xml
		
	def put_person(self, xml):
		res = self._get_page("/people.xml", "POST", xml)
		if res[0] != "201":
			return False # Could not submit data
		dom = parseString(res[1])
		id = dom.getElementsByTagName("id")[0]
		return int(id.childNodes[0].data)
		
	def get_tags(self):
		""" Return a dictionary with id:name pairs containing all tags.
		"""
		taglist = {}
		res = self._get_page("/tags.xml")
		if res[0] != "200":
			return False # Could not get tags
		xml = res[1]
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
		res = self._get_page("/%s/%d/tags.xml" %(type, id), 
			"POST", "<name>%s</name>" % (name))
		if res[0] != "201":
			return False
		dom = parseString(res[1])
		id = dom.getElementsByTagName("id")[0]
		return int(id.childNodes[0].data)



	def get_parties(self, tag_id):
		
		parties = []
		res = self._get_page("/tags/%d.xml" % (int(tag_id)))
		if res[0] != "200":
			return False
		dom = parseString(res[1])
		for person in dom.getElementsByTagName("person"):
			parties.append(self._parse_person(person))
		return parties

	def create_membership(self, user_id, group_id):
		xml = """<membership>
					<user_id type="integer">%d</user_id>
					<group_id type="integer">%d</group_id>
				</membership>""" % (user_id, group_id)
		res = self._get_page("/memberships.xml", "POST", xml)
		if res[0] != "201":
			return False
		return True

	def put_note(self, type, id, note):
		xml = """<note>
					<body>%s</body>
					<visible-to>Everyone</visible-to>
				</note>""" % (note)
		res = self._get_page("/%s/%d/notes.xml" %(type, id), "POST", xml)
		if res[0] != "201":
			return False
		return True


