from scarf import app
from flask import redirect, url_for, render_template, session, escape, request, flash
from scarflib import redirect_back, pagedata, NoUser, siteuser
from sql import read, doquery

def get_users():
    sql = read('users')
    result = doquery(sql)

    users = []

    for user in result:
        users.append(siteuser.create(user[1]))

    return users
@app.route('/admin')
def admin_users():
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 255:
        return redirect(url_for('accessdenied'))

    pd.title = "Admin" 

    pd.users = get_users()

    return render_template('admin.html', pd=pd)

@app.route('/admin/users/<user>/accesslevel/<level>')
def admin_set_accesslevel(user, level):
    pd = pagedata()

    if 'username' not in session or pd.authuser.accesslevel < 10:
        return redirect(url_for('accessdenied'))

    if session['username'] == user:
        app.logger.error('Accesslevel change was denied for user: ' + pd.authuser.username)
        flash("WTF, you can't edit your own permissions!")
        return redirect_back('index')

    if pd.authuser.accesslevel != 255 and pd.authuser.accesslevel <= level:
        app.logger.error('Accesslevel change was denied for user: ' + pd.authuser.username)
        flash("No.")
        return redirect_back('index')

    try:
        moduser = siteuser.create(escape(user))

    except NoUser:
        app.logger.error('Accesslevel change attempted for invalid user by: ' + pd.authuser.username)
        pd.title = "User does not exist"
        pd.errortext = "The user does not exist"
        return render_template('error.html', pd=pd)

    if pd.authuser.accesslevel != 255 and moduser.accesslevel >= pd.authuser.accesslevel:
        flash("Please contact an admin to modify this user's account.")
        return redirect_back('index')

    moduser.newaccesslevel(escape(level))
    app.logger.info('Accesslevel change for ' + user)
    flash('User ' + user + '\'s accesslevel has been set to ' + level)

    return redirect_back('/admin')