CSpace is peer-to-peer communication software of unknown origin, claiming to
offer users an unusually high degree of privacy.

CSpace was described by 
[anonymous-p2p.org](http://www.anonymous-p2p.org/cspace.html):

> CSpace provides a platform for secure, decentralized, user-to-user
> communication over the internet. The driving idea behind the CSpace
> platform is to provide a connect(user,service) primitive, similar to the
> sockets API connect(ip,port). Applications built on top of CSpace can
> simply invoke connect(user,service) to establish a connection. The CSpace
> platform will take care of locating the user and creating a secure,
> nat/firewall friendly connection. Thus the application developers are
> relieved of the burden of connection establishment, and can focus on the
> application-level logic!
> 
> CSpace is developed in Python. It uses OpenSSL for crypto, and Qt for the
> GUI.  CSpace is licensed under the GPL.
> 
> *What applications are available now?*
> 
> The following applications are currently available with CSpace:
> 
> * Text Chat
> * File Transfer
> * Remote Desktop (based on VNC)
> 
> *How does it work?*
> 
> Here are some of the salient points regarding the CSpace architecture:
> 
> User Identity
> 
> * All users create 2048-bit RSA keys for themselves.
> * A user is uniquely identified by his RSA public key.
> * Every user has a contact list, which is just a list of public keys known
> 	to that user.
> * A user assigns names to the public keys in his contact list. This is done
> 	because it is easier to display & manage names rather than raw public
> 	keys.
> * CSpace ensures that there are no duplicate names present in the contact
> 	list.  This is done to allow a contact name to uniquely identify a
> 	public key in the contact list.
> * To help with the exchange of public keys between users, a key server is
> 	used (somewhat like PGP key servers).
> 
> Decentralized Network
> 
> * A Distributed Hash Table (DHT) based on the Kademlia protocol is used.
> * When a user goes online, a mapping from his public key to his ip-address
> 	is created in the DHT.
> * CSpace also registers with third party routers, so that the user can
> 	receive connections even if he is behind a nat/firewall.
> 
> Connection Process
> 
> * When an application wants to utilize the CSpace platform, it establishes
> 	a local connection to the CSpace instance, and issues a connect
> 	request, say, something along the lines of connect(alice,TextChat).
> * CSpace obtains the destination user's public key by looking up the name
> 	in the contact list.
> * The DHT is used to obtain the destination user's network location (ip
> 	address).
> * A TCP connection is established to the destination user's network
> 	address. In case the destination user is behind a nat/firewall, then a
> 	proxied connection is established using a third party router.
> * A secure channel is established using the TLS protocol.
> * The service name which was requested (say TextChat) is sent over the
> 	secure channel, and the destination CSpace instance responds with a
> 	success code.
> * The application which issued the connect request is notified about the
> 	successful connection. CSpace proxies the data between the local
> 	application and the secure channel. Thus the application only sees a
> 	plain TCP connection to localhost.

It is unknown whether these descriptions were written by the CSpace author(s).



## Background

CSpace was brought to public attention by mention in a document
([www.spiegel.de/media/media-35535.pdf](http://www.spiegel.de/media/media-35535.pdf),
page 20) purportedly leaked by NSA whistleblower [Edward
Snowden](http://en.wikipedia.org/wiki/Edward_Snowden).  The document suggests
use of CSpace, in conjunction with other named tools, may result in NSA's
"near-total loss/lack of insight to target communications, presence".  

The CSpace source code was downloaded from
[cspace.aabdalla.com](http://cspace.aabdalla.com/releases/cspace-0.1.27.tar.gz)
on 31 December 2014.  The code was freely available to the public for download,
and no copyright or license statements could be found therein or on the hosting
site.  I am therefore making a good faith assumption that it is public domain
(or analagous legal construct, as appropriate).   The [draft CSpace Wikipedia
page](http://en.wikipedia.org/wiki/Draft:CSpace) lists the license as GPL, but
I can find no other evidence to support that claim.

If you find CSpace interesting, you may wish to clone this repo to your local
computer, in case it gets censored in the future.


## History

The following history was
[provided](https://github.com/jmcvetta/cspace/issues/2) by
[@rep-movsd](https://github.com/rep-movsd):

> CSpace was the brain child of Tachyon Technologies, an Indian startup, where I
> worked for a few years.
> 
> Tachyon was started by a couple of IIT-Madras graduates, who wanted to build
> great software products rather than become an IT shop as most other Indian
> companies did.
> 
> These two guys:
> 
> * Ram Prakash H ( developer of Quillpad) -
> 	http://www2.technologyreview.com/TR35/Profile.aspx?TRID=868
> * KS Sreeram (Creator of the Clay programming language)
> 	https://www.reddit.com/r/programming/comments/ctmxx/the_clay_programming_language/
> 
> I can give you some history about it:
> 
> In 2002, we had built a standalone application called CSpace, that was a
> multiparty conference tool, supporting a shared whiteboard, document sharing,
> audio conferencing and application sharing (remote viewing) . The product was
> branded as Expressmeet and licensed to Sify Technologies.
> 
> However we wanted to keep the CSpace name for something even better. So Sreeram
> decided to build a completely secure P2P platform based on Chord networks. The
> idea was that instead of having a model where you connect to IP:Port, you
> should be able to connect to User:Service and the CSpace platform would do the
> rest, with unholy levels of security.
> 
> It was developed in python and QT and the product worked wonderfully for a few
> years. But the problem was that there would always have to be some sort of
> central registry of logged on users. There was a server provided by Sify
> Infotech for a while, but I believe that went away and CSpace languished.


## Disclaimers

I did not write CSpace; do not use it; do not have any insight into its
original authorship or purposes; have not reviewed the code in any meaningful
way; cannot help you with bugs/support/etc; and do not assert the truth or
falsehood of the CSpace privacy claims.  

I have *no freakin' idea* if this software works at all.  I have uploaded the
source to Github to foster healthy, open civic debate.

There is a decent chance that users of this software will experience
increased surveillance and resultingly *decreased* personal privacy.

**Do not use this software**; or if you must, use it at your own risk.  
