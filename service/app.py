from flask import Flask, request, jsonify

app = Flask(__name__)

# This represents our internal database for mock service
inventory = {
    "laptop": {"price": 1000, "stock": 10},
    "mouse": {"price": 25, "stock": 50}
}

@app.route('/purchase', methods=['POST'])
def purchase():
    data = request.json
    item = data.get("item")
    qty = data.get("quantity", 0)

    if item in inventory and inventory[item]["stock"] >= qty:
        inventory[item]["stock"] -= qty
        return jsonify({"status": "success", "message": f"Purchased {qty} {item}(s)"}), 200
    
    return jsonify({"status": "error", "message": "Insufficient stock or item not found"}), 400


@app.route('/items/<item_name>', methods=['GET'])
def get_item(item_name):
    inventory = {
        "laptop": {"price": 1000},
        "mouse": {"price": 25}
    }
    # Return the item if found, or a default price of 0
    return jsonify(inventory.get(item_name, {"price": 0}))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)