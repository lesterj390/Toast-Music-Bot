import sqlite3


class Database:
    def __init__(self):
        self.filename = "serverData.db"
        self.conn = sqlite3.connect(self.filename)

    def CreateTables(self) -> None:
        """
        This function creates the sql tables which hold server info on which chat is
        prefixless.
        """

        self.conn.execute("""CREATE TABLE IF NOT EXISTS Servers
                        ( GUILD_ID          VARCHAR(32) NOT NULL,
                          CHAT_ID           VARCHAR(32) NOT NULL,
                          PRIMARY KEY (GUILD_ID) );""")

    def __setitem__(self, key, value):
        """
        This function adds an entry into the Database with GUILD_ID key and CHAT_ID
        value.
        """
        self.conn.execute(f"""INSERT INTO Servers
                              VALUES ({key}, {value})""")
        self.conn.commit()

    def __getitem__(self, item) -> bool:
        """
        This functions returns a boolean representing if item GUILD_ID is in the Database
        """
        value = self.conn.execute(f"""SELECT EXISTS(SELECT * FROM Servers WHERE GUILD_ID = {item})""")
        value = value.fetchone()

        return bool(value[0])

    def GetChatID(self, targetGuildID: str) -> str:
        """
        This function uses the server Database array and targetGuildID (server id)
        number to get the id of the prefixless channel.

        :param targetGuildID:
        :return: the chat_id if it exists in the Database and None otherwise
        """

        chatID = self.conn.execute(f"""SELECT CHAT_ID FROM Servers
                                       WHERE GUILD_ID = {targetGuildID}""").fetchone()

        if chatID == None:
            return False

        return chatID[0]

    def UpdateChatID(self, targetGuildID: str, newChatID: str):
        """
        This function uses the server Database, the targetGuildID (server id) and the
        newChatID to update the prefixless channel id in the event it gets remade.

        :param targetGuildID:
        :param newChatID:
        """
        if self[targetGuildID]:
            self.conn.execute(f"""UPDATE Servers
                                  SET CHAT_ID = {newChatID}
                                  WHERE GUILD_ID = {targetGuildID}""")
            self.conn.commit()
