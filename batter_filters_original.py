def batter_filters():
    athlete_id = request.args.get('id')
    if not athlete_id:
        return jsonify({"formats": [], "leagues": [], "venues": [], "phases": ["Powerplay (1-6)", "Middle Overs (7-15)", "Death Overs (16-20)"], "opponents": []})