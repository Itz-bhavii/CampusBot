package com.bhavesh.campusbot.Repositorys;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.bhavesh.campusbot.Entities.ChatMessage;


@Repository
public interface ChatMessageRepository extends JpaRepository<ChatMessage,UUID>{

    List<ChatMessage> findByConversationIdOrderByTimestampAsc(UUID conversationId);
}
