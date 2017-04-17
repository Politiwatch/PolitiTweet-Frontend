import database

accounts = []

def load_vitals():
    print("Loading vitals into cache...")
    # will return array of IDs (as integers)
    accounts_in_db = database.getAllAccountsInDatabase()
    for account in accounts_in_db:
        # load account data
        data = database.getAccountFromDatabase(account)
        # ...and metadata
        metadata = database.getAccountMetadata(account)
        # set metadata parameters in account data... hopefully no override! TODO
        for key in metadata.keys():
            data[key] = metadata[key]
        accounts.append(data)
    print("...done!")


def get_account(id):
    data = database.getAccountFromDatabase(id)
    # ...and metadata
    metadata = database.getAccountMetadata(id)
    # set metadata parameters in account data... hopefully no override! TODO
    for key in metadata.keys():
        data[key] = metadata[key]
    if "description" not in data:
        data["description"] = "This figure does not have a description."
    if "location" not in data:
        data["location"] = "n/a"
    return data

load_vitals()
