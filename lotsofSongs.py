from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup_catalog import Base, User, Genre, Song
 
engine = create_engine('sqlite:///catalogwithusers.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

Vince = User(name = "Vince", email="zw@gmail.com", picture = "https://s-media-cache-ak0.pinimg.com/736x/81/10/7c/81107cd849cd034de861d00af80004fc.jpg")
session.add(Vince)
session.commit()

#Item for POP
genre1 = Genre(user_id = 1, name = "POP")

session.add(genre1)
session.commit()

item1 = Song(name = "All of Me", url = "https://www.youtube.com/watch?v=450p7goxZqg", description = "a song by American recording artist John Legend from his fourth studio album Love in the Future", artist = "John Legend", genre = genre1, owner_id = 1)

session.add(item1)
session.commit()


# Item for Country
genre2 = Genre(user_id = 1, name = "Country")

session.add(genre2)
session.commit()

item1 = Song(name = "Crash My Party", url = "https://www.youtube.com/watch?v=1WEpLzsdEeY" , description = "Crash My Party is the fourth studio album by American country music artist Luke Bryan. It was released on August 13, 2013 via Capitol Nashville Its first single, the title track, reached number one on the Billboard Country Airplay chart", artist = "Luke Bryan", owner_id = 1, genre = genre2)

session.add(item1)
session.commit()


# Item for Hip Pop
genre3 = Genre(user_id = 1, name = "Hip Pop")

session.add(genre3)
session.commit()

item1 = Song(name = "Thrift Shop",url = "https://www.youtube.com/watch?v=QK8mJJJvaes", description = "Released on August 27, 2012 as Macklemore eighth career single and the fourth single from their debut studio album The Heist", artist = "Macklemore & Ryan Lewis", owner_id = 1, genre = genre3)

session.add(item1)
session.commit()


# Item for R&B
genre4 = Genre(user_id = 1, name = "R&B")

session.add(genre4)
session.commit()

item1 = Song(name = "Wicked Games", url = "https://www.youtube.com/watch?v=O1OTWCd40bc", description = "The debut single by Canadian singer The Weeknd. It was recorded at Site Sound Studios and mixed at Liberty Studios in Toronto", artist = "The Weeknd", owner_id = 1, genre = genre4)

session.add(item1)
session.commit()


print "added Songs!"
