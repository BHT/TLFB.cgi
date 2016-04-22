SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
CREATE DATABASE IF NOT EXISTS `uvabht_tlfb` DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
USE `uvabht_tlfb`;

DROP TABLE IF EXISTS `marker_days`;
CREATE TABLE `marker_days` (
  `id` int(11) NOT NULL,
  `participant_id` varchar(12) DEFAULT NULL,
  `date` varchar(10) DEFAULT NULL,
  `description` varchar(150) DEFAULT NULL
) ENGINE=MyISAM DEFAULT CHARSET=latin1;

DROP TABLE IF EXISTS `tlfb`;
CREATE TABLE `tlfb` (
  `id` int(11) NOT NULL,
  `participant_id` varchar(12) DEFAULT NULL,
  `date` varchar(10) DEFAULT NULL,
  `hours` int(11) DEFAULT NULL,
  `drinks` int(11) DEFAULT NULL,
  `joints` int(11) DEFAULT NULL,
  `insert_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=MyISAM DEFAULT CHARSET=latin1;


ALTER TABLE `marker_days`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `tlfb`
  ADD PRIMARY KEY (`id`);


ALTER TABLE `marker_days`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
ALTER TABLE `tlfb`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT2;
