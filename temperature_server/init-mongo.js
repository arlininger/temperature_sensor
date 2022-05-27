db.createUser(
	{
		user: "temperature-root",
		pwd: "sHFyBLZBd5yLhCDG2GIgvQ",
		roles : [
			{
				role: "readWrite",
				db: "temperature-data"
			}
		]
	}
)