package com.bhavesh.campusbot.Utils;

import java.util.UUID;

public final class UuidUtils {

    
    public static boolean isUUidEmpty(UUID uuid){
        return uuid == null || (uuid.getMostSignificantBits() == 0L && uuid.getLeastSignificantBits() ==0L);
    }
}
