from app import app
from app import imagemanipulation as im
from app import tools
from flask import render_template, redirect, request, session, send_from_directory, abort
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from flask.helpers import flash
import shutil
import smtplib



@app.route('/')
def home():
    return render_template('index.html')


@app.route('/input')
def input():
    return render_template('input.html')


@app.route('/uploadInput', methods=["GET", "POST"])
def uploadInput():
    if request.method == "POST":
        if request.files:
            timestamped = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            folder = request.files.getlist("input-folder-2[]")
            email = request.form.get("email")
            sendaddress = app.config["EMAIL_USERNAME"]
            sendpassword = app.config["EMAIL_PASSWORD"]
            if email:
                with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                    smtp.login(sendaddress, sendpassword)
                    subject = 'ecSeg is Running'
                    body = f'Dear User: \n\necSeg is currently running on your input images and parameters. This may take some time to complete. Another email will be sent when finished and visualizations are ready. \n\nDo not reply to this email. If you have a problem with the ecDNA Analytics webtool, create an issue on github (linked below). \nhttps://github.com/MihirBafna/ecDNA-Analytics/issues/new \n\n- ecDNA Analytics Support'
                    msg = f'Subject: {subject}\n\n{body}'
                    smtp.sendmail(sendaddress, email, msg)
            print(email)
            folderpath = os.path.join(
                app.config["IMAGE_UPLOADS"], "ecSegOutput", timestamped)
            os.makedirs(folderpath)
            print(folderpath)
            for file in folder:
                print(file.filename)
                if file.filename == "":
                    try:
                        shutil.rmtree(folderpath)
                        flash(
                            f'No folder was selected.', 'warning')
                    except OSError as e:
                        print("Error: %s : %s" % (folderpath, e.strerror))
                    return redirect('/input')
                if im.allowed_image(file.filename, True):
                    path = os.path.join(
                        app.config["IMAGE_UPLOADS"], "ecSegOutput", timestamped, '/'.join(file.filename.split('/')[1:]))
                    file.save(path)
                    print("Image saved " + path)
                else:
                    print("not allowed")
        # check if folder is correct here
        if im.correctInputFolderStructure(folderpath):
            flash(f'ecSeg has been run succesfully. Folder {timestamped} has been created and visualized. Save this name for future reference.', 'success')
        else:
            try:
                shutil.rmtree(folderpath)
                flash(f'Invalid folder. Folder name {timestamped} could not be created and visualized. Check for proper input folder format.', 'danger')
            except OSError as e:
                print("Error: %s : %s" % (folderpath, e.strerror))
            return redirect('/input')
        # RUN ECSEG HERE
        tools.runecSeg(folderpath,1)
        im.reorganizeOutput(timestamped)
        path = os.path.join(app.config["IMAGE_UPLOADS"],
                            "ecSegOutput", timestamped, "orig")+'/'
        session['folder'] = timestamped
        im.tiffToPNG(timestamped)
        session['imagelist'] = im.imglist(path)
        session['imagename'] = session['imagelist'][0]
        if email:
            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(sendaddress, sendpassword)
                subject = 'Your Visualization is Ready'
                body = f'Dear User: \n\necSeg was run successfully on your given input images and parameters. You have been redirected to the \'visualize\' page. Save the folder name {timestamped} for future reference and visualization. \n\nDo not reply to this email. If you have a problem with the ecDNA Analytics webtool, create an issue on github (linked below). \nhttps://github.com/MihirBafna/ecDNA-Analytics/issues/new \n\n- ecDNA Analytics Support'
                msg = f'Subject: {subject}\n\n{body}'
                smtp.sendmail(sendaddress, email, msg)
        return redirect('/visualize')
    else:
        return render_template('input.html')



@app.route('/uploadecSeg', methods=["GET", "POST"])
def uploadecSeg():
    if request.method == "POST":
        if request.files:
            folder = request.files.getlist("input-folder-3[]")
            timestamped = datetime.now().strftime('%Y-%m-%d_%H%M%S')
            directorypath = os.path.join(
                app.config["IMAGE_UPLOADS"], "ecSegOutput", timestamped)
            origpath = os.path.join(
                app.config["IMAGE_UPLOADS"], "ecSegOutput", timestamped, "orig")
            os.makedirs(origpath)
            os.mkdir(os.path.join(
                app.config["IMAGE_UPLOADS"], "ecSegOutput", timestamped, "dapi"))
            os.mkdir(os.path.join(
                app.config["IMAGE_UPLOADS"], "ecSegOutput", timestamped, "labels"))
            for file in folder:
                if file.filename == "":
                    try:
                        shutil.rmtree(directorypath)
                        flash(
                            f'No folder was selected.', 'warning')
                    except OSError as e:
                        print("Error: %s : %s" % (directorypath, e.strerror))
                    return redirect('/input')
                if im.allowed_image(file.filename, False):
                    path = os.path.join(
                        app.config["IMAGE_UPLOADS"], "ecSegOutput", timestamped, '/'.join(file.filename.split('/')[1:]))
                    file.save(path)
                    print(file.filename+" saved")
                else:
                    print(file.filename+" not allowed")
        im.tiffToPNG(timestamped)
        if im.correctOutputFolderStructure(directorypath):  # check if folder is correct here
            flash(f'Folder {timestamped} has been created and visualized. Save this name for future reference.', 'success')
        else:
            try:
                shutil.rmtree(directorypath)
                flash(f'Invalid folder. Folder name {timestamped} could not be created and visualized. Check for proper output folder format.', 'danger')
            except OSError as e:
                print("Error: %s : %s" % (directorypath, e.strerror))
            return redirect('/input')
        path = os.path.join(app.config["IMAGE_UPLOADS"],
                            "ecSegOutput", timestamped, "orig")+'/'
        session['folder'] = timestamped
        session['imagelist'] = im.imglist(path)
        session['imagename'] = session['imagelist'][0]
        return redirect('/visualize')
    else:
        return render_template('input.html')


@app.route('/visualize/<img>')
def newimgselect(img):
    session['imagename'] = img
    return redirect('/visualize')



@app.route('/visualize')
def visualize():
    return render_template('visualize.html', images=session['imagelist'], folder=session['folder'], imgname=session['imagename'])


@app.route('/directvisualize', methods=["GET", "POST"])
def directVisualize():
    if request.method=="POST":
        folder = request.form['folder']
        print(folder)
        path = os.path.join(app.config["IMAGE_UPLOADS"],"ecSegOutput", folder, "orig")+'/'
        if os.path.exists(path):
            flash(
                f'Folder {folder} was visualized.', 'success')
            session['folder'] = folder
            session['imagelist'] = im.imglist(path)
            session['imagename'] = session['imagelist'][0]
            return redirect('/visualize')
        else:
            flash(f'Invalid folder. Folder name {folder} not recognized.', 'danger')
            return render_template('input.html')
    else:
        return render_template('input.html')

@app.route('/downloadAll/<folder>')
def downloadAll(folder):
    try:   
        path = os.path.join(app.config["IMAGE_UPLOADS"],
                                    "ecSegOutput", folder)+'/'
        final = im.compressAll(path, folder)
        filename = final.split('/')[-1]
        outpath = '/'.join(final.split('/')[1:-1])
        print(outpath,filename)
        return send_from_directory(outpath, filename=filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)


@app.route('/downloadIMG/<folder>/<imgname>')
def downloadIMG(imgname, folder):
    try:
        path = os.path.join(app.config["IMAGE_UPLOADS"],
                            "ecSegOutput", folder)+'/'
        final = im.compressIMG(path, imgname)
        filename = final.split('/')[-1]
        outpath = '/'.join(final.split('/')[1:-1])
        print(outpath, filename)
        return send_from_directory(outpath, filename=filename, as_attachment=True)
    except FileNotFoundError:
        abort(404)

@app.route('/clearclientcache')
def clearClientCache():
    path = app.config["IMAGE_DOWNLOADS"]
    numfiles = im.removeClientCache(path)
    return redirect('/visualize')

@app.route('/mpDetector')
def metaDetect():
    return render_template('index.html')



