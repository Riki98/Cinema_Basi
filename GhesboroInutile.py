#### SCRIVERE HTML ####
datafile = open('base_film.html', "r+")
for line in datafile:
    if "<!--Title-->" in line:
        datafile.write("\n<h1>" + newTitle + "</h1>")
    elif "<!--Genre-->" in line:
        datafile.write("\n<h3>" + newGenre + "</h3>")
    elif "<!--Director-->" in line:
        datafile.write("\n<p>" + newMovDir + "</p>")
    elif "<!--Actors-->" in line:
        datafile.write("\n<p>" + newGenre + "</p>")
    elif "<!--Typology-->" in line:
        datafile.write("\n<p>" + is3d + "</p>")
    elif "<!--Img-->" in line:
        datafile.write("\n<img src=\"/static/img/Locandine/TheGrudge.png\" class=\"dimensione\" alt="">")
    elif "<!--Plot-->" in line:
        datafile.write("\n<p>" + newPlot + "</p>")
    elif "<!--firstDate-->" in line:
        datafile.write("\n<p>" + newStartData + "</p>")
    elif "<!--lastDate-->" in line:
        datafile.write("\n<p>" + newLastData + "</p>")
    elif "<!--Duration-->" in line:
        datafile.write("\n<p>" + newDuration + "</p>")
    elif "<!--countryOfOrigin-->" in line:
        datafile.write("\n<p>" + newCountry + "</p>")
    elif "<!--Year-->" in line:
        datafile.write("\n<p>" + newYearPubb + "</p>")
    elif "<!--minAge-->" in line:
        datafile.write("\n<p>" + newMinAge + "</p>")

datafile.close()

# Aquisizione e salvataggio della locandina
    cv2.imwrite(r'/static/img/Locandine', request.form["newImage"])