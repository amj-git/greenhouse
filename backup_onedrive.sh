cd /home/pi/greenhouse
for f in ${1:-./db/*.db}
do
    echo "Backing up $f------------------------"
    bf="${f%.*}-backup.db"
    echo "Creating backup file $bf"
    sqlite3 "$f" ".timeout 10000" ".backup '$bf'"
    echo "Copying $bf to gh_backup_onedrive:gh_backup"
    rclone copy "$bf" gh_backup_onedrive:gh_backup
    echo "Deleting $bf"
    rm "$bf"
    echo "Backing up $f COMPLETE--------------------"

done
